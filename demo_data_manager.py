# demo_data_manager.py
import logging
from pathlib import Path

import pandas as pd


class DemoDataManager:
    def __init__(self, data_dir="demo_data"):
        self.data_dir = Path(data_dir)
        self.structure = self._build_structure()

    def get_grades(self):
        return sorted(self.structure.keys())

    def get_subjects(self, grade):
        return sorted(self.structure.get(grade, {}).keys())

    def get_assignments(self, grade, subject):
        return sorted(self.structure.get(grade, {}).get(subject, []))

    def check_data_exists(self):
        return self.data_dir.exists() and bool(self.structure)

    def get_demo_file(self, grade, subject, assignment):
        path = self._dataset_path(grade, subject, assignment)
        if path and path.exists():
            return str(path)
        logging.warning("Demo dataset missing for %s/%s/%s", grade, subject, assignment)
        return None

    def load_csv(self, grade, subject, assignment):
        dataset_path = self._dataset_path(grade, subject, assignment)
        if not dataset_path or not dataset_path.exists():
            logging.error("Demo CSV not found at path: %s", dataset_path)
            return None, 0, 0, 0

        expected_headers = ["Student Name", "Score", "Feedback", "Rubric"]

        try:
            df = pd.read_csv(dataset_path)
            if list(df.columns) != expected_headers:
                logging.error(
                    "CSV header mismatch in %s. Expected: %s",
                    dataset_path,
                    expected_headers
                )
                return None, 0, 0, 0

            total = len(df)
            submitted_count = df[df["Score"] != "Not submitted"].shape[0]
            missing_count = total - submitted_count

            return df, submitted_count, total, missing_count

        except Exception as e:
            logging.error("Failed to load or parse CSV %s: %s", dataset_path, e)
            return None, 0, 0, 0

    def get_dataset_summary(self, grade, subject, assignment):
        df, submitted, total, missing = self.load_csv(grade, subject, assignment)
        if df is None:
            return None
        return {"submitted": submitted, "total": total, "missing": missing}

    # --- Internal helpers ---
    def _build_structure(self):
        structure = {}
        if not self.data_dir.exists():
            logging.warning("Demo data directory not found at %s", self.data_dir)
            return structure

        for grade_dir in sorted(self.data_dir.iterdir(), key=lambda p: p.name):
            if not grade_dir.is_dir() or grade_dir.name.startswith('.'):
                continue

            subjects = {}
            for subject_dir in sorted(grade_dir.iterdir(), key=lambda p: p.name):
                if not subject_dir.is_dir() or subject_dir.name.startswith('.'):
                    continue

                assignments = sorted(
                    csv_file.stem
                    for csv_file in subject_dir.glob("*.csv")
                    if csv_file.is_file()
                )

                if assignments:
                    subjects[subject_dir.name] = assignments

            if subjects:
                structure[grade_dir.name] = subjects

        return structure

    def _dataset_path(self, grade, subject, assignment):
        if not all([grade, subject, assignment]):
            return None
        return self.data_dir / grade / subject / f"{assignment}.csv"
