"""Training entry point for the 10-model comparison.

Implemented in Sprint 2 after the ETL pipeline is in place.
"""


MODEL_NAMES = [
    "logistic_regression",
    "decision_tree",
    "random_forest",
    "gradient_boosting",
    "xgboost",
    "lightgbm",
    "catboost",
    "svm",
    "knn",
    "mlp",
]

METRIC = "f1_macro"
CV_FOLDS = 5


def main() -> None:
    raise NotImplementedError("ML training belongs to Sprint 2.")


if __name__ == "__main__":
    main()
