"""Perceptra's local dashboard. NLP and scoring belong to the analysis service."""

import logging
import math

import streamlit as st

from perceptra.analysis import analyze_product
from perceptra.ingestion.dataset_loader import load_manifest


def clear_analysis():
    for key in ("analysis_result", "analysis_error", "aspect_selection", "review_filter",
                "review_search", "review_page", "review_filter_signature"):
        st.session_state.pop(key, None)


def review_rows(reviews):
    return [{"Review ID": row["review_id"], "Original review": row["original_text"],
             "Sentiment": row["prediction"]["label"].title(),
             "VADER compound": row["prediction"]["sentiment_score"],
             "Product ID": row["product_id"]} for row in reviews]


def render_results(result):
    product = result["product"]
    st.subheader(product["name"])
    st.caption(f"{product['product_id']} · Local VADER analysis · Historical research dataset")
    if result["aspect_analysis"]["status"] in ("missing_resources", "failed"):
        st.warning("Sentiment results are ready. Aspect estimates are unavailable; open Aspect estimates for details.")
    elif result["aspect_analysis"]["status"] == "partial":
        st.warning("Some reviews lacked usable aspect evidence. Estimates use only reviews with valid predictions.")
    st.caption(
        f"{result['original_review_count']} prepared reviews · "
        f"{result['rejected_review_count']} filtered · {result['duplicate_count']} duplicates removed"
    )
    if result["status"] == "no_reviews" or not result["analyzed_count"]:
        st.info("No usable reviews remain for this product. Try another product or check the prepared dataset.")
        return

    metrics = st.columns(5)
    metrics[0].metric("Reviews analyzed", result["analyzed_count"])
    rating = result["perception_rating"]
    metrics[1].metric("Perception rating", f"{rating:.2f}/10" if rating is not None else "Unavailable")
    for column, label in zip(metrics[2:], ("positive", "negative", "neutral")):
        column.metric(label.title(), f"{result['sentiment_percentages'][label]:.1f}%")
    st.caption("Perception is an NLP-derived indicator, not an average customer star rating or a probability.")

    overview, aspect_tab, explorer = st.tabs(["Sentiment overview", "Aspect estimates", "Customer reviews"])
    with overview:
        st.subheader("Sentiment distribution")
        counts = [{"Sentiment": label.title(), "Reviews": result["sentiment_counts"][label]}
                  for label in ("positive", "negative", "neutral")]
        chart, count_table = st.columns([2, 1])
        with chart:
            st.vega_lite_chart(counts, {
                "height": 230,
                "mark": {"type": "bar", "cornerRadiusEnd": 3},
                "encoding": {
                    "y": {"field": "Sentiment", "type": "nominal", "title": None,
                          "sort": ["Positive", "Negative", "Neutral"]},
                    "x": {"field": "Reviews", "type": "quantitative", "axis": {"tickMinStep": 1}},
                    "color": {"value": "#0f766e"},
                    "tooltip": [{"field": "Sentiment"}, {"field": "Reviews", "type": "quantitative"}],
                },
            })
        with count_table:
            st.dataframe(counts, hide_index=True)
        st.subheader("Supporting customer reviews")
        for column, label in zip(st.columns(2), ("positive", "negative")):
            with column:
                st.markdown(f"**{label.title()} evidence**")
                examples = sorted((row for row in result["scored_reviews"] if row["prediction"]["label"] == label),
                                  key=lambda row: row["prediction"]["sentiment_score"], reverse=label == "positive")[:1]
                if not examples:
                    st.info(f"No {label} review examples in this result.")
                for row in examples:
                    with st.container(border=True):
                        st.caption(f"Sentiment score {row['prediction']['sentiment_score']:.4f}")
                        text = row["original_text"]
                        st.write(text[:280] + ("…" if len(text) > 280 else ""))
                        with st.expander("Read full review"):
                            st.caption(row["review_id"])
                            st.write(text)

    with aspect_tab:
        st.subheader("Aspect-level estimates")
        analysis = result["aspect_analysis"]
        st.info(analysis["explanation"])
        if analysis["used_fallback"]:
            st.caption("Frequent-noun fallback was used because fewer than five dimension-list terms were found.")
        aspects = analysis["aspects"]
        if not aspects:
            if analysis["status"] == "missing_resources":
                st.info("Aspect estimates are unavailable until the local NLTK resources are prepared. Sentiment results remain available.")
                for warning in analysis["warnings"]:
                    st.warning(warning)
            elif analysis["status"] == "failed":
                st.info("Aspect processing was unavailable for this run. Sentiment results remain available.")
            else:
                st.info("No repeated aspects have sufficient scored-review evidence in this product's reviews.")
        else:
            st.dataframe([
                {"Aspect": item["aspect"].title(), "Estimated rating /10": round(item["rating"], 2),
                 "Average sentiment": round(item["avg_sentiment"], 4),
                 "Supporting reviews": item["supporting_review_count"], "Evidence volume": item["evidence_volume"]}
                for item in aspects
            ], hide_index=True)
            st.caption("Evidence volume: Low <7 reviews, Medium 7–14, High ≥15. It does not measure model accuracy.")
            with st.expander("Inspect supporting review evidence"):
                selected = st.selectbox("Aspect", options=[item["aspect"] for item in aspects],
                                        format_func=str.title, key="aspect_selection")
                aspect = next(item for item in aspects if item["aspect"] == selected)
                ids = set(aspect["supporting_review_ids"])
                supporting = [row for row in result["scored_reviews"] if row["review_id"] in ids]
                st.caption(f"Showing up to 10 of {aspect['supporting_review_count']} supporting reviews.")
                st.dataframe(review_rows(supporting[:10]), hide_index=True, height=360)

    with explorer:
        st.subheader("Customer review explorer")
        filter_column, search_column, page_column = st.columns([1, 2, 0.6])
        with filter_column:
            selection = st.selectbox("Filter sentiment", ["All sentiments", "Positive", "Negative", "Neutral"], key="review_filter")
        with search_column:
            search = st.text_input("Search review text", placeholder="Search the original customer reviews", key="review_search")
        rows = result["scored_reviews"]
        if selection != "All sentiments":
            rows = [row for row in rows if row["prediction"]["label"] == selection.lower()]
        if search.strip():
            rows = [row for row in rows if search.strip().casefold() in row["original_text"].casefold()]
        signature = (product["product_id"], selection, search)
        if st.session_state.get("review_filter_signature") != signature:
            st.session_state.pop("review_page", None)
            st.session_state["review_filter_signature"] = signature
        if rows:
            pages = max(1, math.ceil(len(rows) / 25))
            with page_column:
                page = st.selectbox("Page", options=list(range(1, pages + 1)), key="review_page")
            start = (page - 1) * 25
            st.caption(f"Reviews {start + 1}–{min(start + 25, len(rows))} of {len(rows)} matching reviews · {result['analyzed_count']} analyzed in total")
            st.dataframe(review_rows(rows[start:start + 25]), hide_index=True, height=420)
        else:
            st.info("No reviews match the selected filters.")

    with st.expander("Method, provenance, and limitations"):
        st.write(f"Engine: {result['model_id']} {result['model_version']} · Score: {result['score_kind']}")
        st.write("VADER compound ranges from −1 to +1. Aspect estimates reuse the sentiment of supporting whole reviews.")
        for limitation in result["limitations"]:
            st.write(f"• {limitation}")
        if result["warnings"]:
            st.markdown("**Processing notes**")
            for warning in result["warnings"]:
                st.write(warning)
        st.caption(f"Prepared dataset SHA-256: {result['dataset_provenance']['processed_sha256']}")


def main():
    st.set_page_config(page_title="Perceptra | Product Perception", page_icon="◉", layout="wide")
    st.header("Perceptra — Product Perception Intelligence")
    st.caption("Understand customer sentiment and explore product strengths through real review evidence.")
    try:
        manifest = load_manifest()
        products = manifest["products"]
    except (OSError, ValueError):
        clear_analysis()
        st.error("The local review dataset is missing or invalid.")
        st.info("Prepare the publisher CSV with .venv\\Scripts\\python.exe scripts/prepare_demo_data.py --input-csv <publisher.csv>.")
        st.stop()
    if not products:
        clear_analysis()
        st.info("No products are available. Prepare a valid product-review dataset to continue.")
        st.stop()
    catalog = {product["product_id"]: product for product in products}
    if st.session_state.get("selected_product") is not None and st.session_state["selected_product"] not in catalog:
        clear_analysis()
        st.session_state.pop("selected_product")
        st.warning("The previous product selection is unavailable. Choose a product from the current dataset.")
    with st.sidebar:
        st.header("Analyze a product")
        selected = st.selectbox("Product", options=list(catalog),
                                format_func=lambda identity: f"Clothing {catalog[identity]['clothing_id']} · {catalog[identity]['category']}", key="selected_product")
        product = catalog[selected]
        st.caption(f"{product['category']} · {product['review_count']} reviews available")
        analyze = st.button("Analyze product", key="analyze", type="primary")
        st.divider()
        st.write(f"**Dataset:** {manifest['dataset_name']}")
        st.write(f"**License:** {manifest['license']}")
        st.link_button("Dataset source", manifest["source_url"])
        st.caption("Historical, anonymized clothing reviews. Product names and brands are not supplied.")
        st.caption("Runs locally · No sign-in required")
    if st.session_state.get("last_selected_product") != selected:
        clear_analysis()
        st.session_state["last_selected_product"] = selected
    if analyze:
        clear_analysis()
        try:
            with st.spinner("Analyzing sentiment and extracting aspect estimates…"):
                result = analyze_product(selected, engine="vader")
                if result["product"]["product_id"] != selected:
                    raise ValueError("The analysis product does not match the selection.")
                st.session_state["analysis_result"] = result
        except Exception:
            logging.getLogger(__name__).exception("Dashboard analysis failed for %s", selected)
            st.session_state["analysis_error"] = (
                "Analysis could not be completed. No results were kept. Try again, or check the local dataset and NLP setup."
            )
    if st.session_state.get("analysis_error"):
        st.error(st.session_state["analysis_error"])
    result = st.session_state.get("analysis_result")
    if result is not None and result["product"]["product_id"] == selected:
        render_results(result)
    elif not st.session_state.get("analysis_error"):
        st.info("Select a product and click Analyze product to calculate sentiment and aspect estimates.")


if __name__ == "__main__":
    main()
