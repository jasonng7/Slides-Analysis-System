ACTION_TITLE_QUALITY_VALUES = [
    "strong_insight_title",
    "descriptive_topic_title",
    "unclear_title",
    "missing_title",
]

SLIDE_TYPE_VALUES = [
    "executive_summary",
    "situation_complication_resolution",
    "issue_tree",
    "hypothesis_tree",
    "market_sizing",
    "competitor_benchmark",
    "2x2_matrix",
    "value_chain",
    "process_flow",
    "operating_model",
    "roadmap",
    "gantt_timeline",
    "waterfall",
    "heatmap",
    "dashboard",
    "financial_summary",
    "recommendation_slide",
    "options_analysis",
    "prioritization_matrix",
    "risk_assessment",
    "stakeholder_map",
    "transformation_journey",
    "implementation_plan",
    "corporate_exercise_overview",
    "merger_acquisition_rationale",
    "merger_acquisition_deal_structure",
    "joint_venture_rationale",
    "joint_venture_operating_model",
    "strategic_partnership_analysis",
    "industry_overview",
    "industry_trend_analysis",
    "market_attractiveness",
    "market_entry_strategy",
    "competitor_landscape",
    "competitor_deep_dive",
    "valuation_comparison",
    "precedent_transaction_analysis",
    "trading_comparable_analysis",
    "synergy_assessment",
    "strategic_fit_assessment",
    "investment_thesis",
    "opportunity_challenge_analysis",
    "growth_options_analysis",
    "business_case_summary",
    "board_decision_paper",
    "other",
]

CHART_TYPE_VALUES = [
    "bar_chart",
    "stacked_bar_chart",
    "line_chart",
    "area_chart",
    "pie_chart",
    "donut_chart",
    "waterfall_chart",
    "bubble_chart",
    "scatter_plot",
    "heatmap",
    "table",
    "matrix",
    "flow_diagram",
    "timeline",
    "gantt_chart",
    "value_chain_diagram",
    "map",
    "dashboard_cards",
    "icon_grid",
    "text_only",
    "mixed_layout",
    "unknown",
]

STORYLINE_TYPE_VALUES = [
    "problem_solution",
    "situation_complication_resolution",
    "insight_evidence_implication",
    "options_evaluation_recommendation",
    "current_state_future_state_gap",
    "market_trend_opportunity",
    "diagnosis_root_cause_action",
    "hypothesis_evidence_conclusion",
    "investment_thesis_supporting_evidence",
    "risk_mitigation",
    "strategy_execution_impact",
    "before_after_bridge",
    "other",
]

AUDIENCE_TYPE_VALUES = [
    "board_of_directors",
    "ceo",
    "executive_committee",
    "head_of_department",
    "corporate_strategy_team",
    "investment_committee",
    "project_steering_committee",
    "internal_management",
    "external_client",
    "general_business_audience",
    "unknown",
]

FALLBACK_BY_FIELD = {
    "action_title_quality": "unclear_title",
    "slide_type": "other",
    "chart_type": "unknown",
    "storyline_type": "other",
    "audience_type": "unknown",
}

ALLOWED_VALUES_BY_FIELD = {
    "action_title_quality": ACTION_TITLE_QUALITY_VALUES,
    "slide_type": SLIDE_TYPE_VALUES,
    "chart_type": CHART_TYPE_VALUES,
    "storyline_type": STORYLINE_TYPE_VALUES,
    "audience_type": AUDIENCE_TYPE_VALUES,
}


def normalize_taxonomy_value(field: str, value: object) -> str:
    allowed_values = ALLOWED_VALUES_BY_FIELD[field]
    fallback = FALLBACK_BY_FIELD[field]
    normalized = str(value or "").strip()
    return normalized if normalized in allowed_values else fallback


def clamp_quality_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return min(100.0, max(0.0, score))
