import json
from datetime import datetime

class SchemaReport:
    """
    Generates full schema report for SOC system.
    """

    def __init__(self, inspector, relationship_detector):
        self.inspector = inspector
        self.relationship_detector = relationship_detector

    def generate_report(self):
        tables = self.inspector.get_tables()
        relations = self.relationship_detector.get_foreign_keys()

        report = {
            "generated_at": str(datetime.now()),
            "tables": tables.to_dict(),
            "relationships": relations.to_dict()
        }

        return report

    def save_report(self, path="schema_report.json"):
        report = self.generate_report()

        with open(path, "w") as f:
            json.dump(report, f, indent=4)

        return path