from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)


class IncidentReportGenerator:
    """
    Generates PDF incident reports for
    detected AeroDrift security incidents.
    """

    def __init__(
        self,
        output_directory: str = "reports",
    ) -> None:
        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def generate(
        self,
        finding: dict,
        remediation_status: str,
    ) -> Path:
        """
        Generate a PDF incident report.
        """

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        report_path = (
            self.output_directory
            / f"aerodrift_incident_{timestamp}.pdf"
        )

        document = SimpleDocTemplate(
            str(report_path),
            pagesize=A4,
        )

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "AeroDrift Incident Report",
                styles["Title"],
            )
        )

        story.append(
            Spacer(1, 20)
        )

        story.append(
            Paragraph(
                "Incident Details",
                styles["Heading2"],
            )
        )

        story.append(
            Paragraph(
                f"Security Group: "
                f"{finding['security_group']}",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"Protocol: {finding['protocol']}",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"Port: {finding['port']}",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"Source: {finding['source']}",
                styles["BodyText"],
            )
        )

        story.append(
            Spacer(1, 15)
        )

        story.append(
            Paragraph(
                "Detection",
                styles["Heading2"],
            )
        )

        story.append(
            Paragraph(
                "Public ingress was detected "
                "from the Internet.",
                styles["BodyText"],
            )
        )

        story.append(
            Spacer(1, 15)
        )

        story.append(
            Paragraph(
                "Remediation",
                styles["Heading2"],
            )
        )

        story.append(
            Paragraph(
                "Action: Revoke unwanted "
                "security group ingress",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"Status: {remediation_status}",
                styles["BodyText"],
            )
        )

        document.build(story)

        return report_path


def generate_incident_report(
    finding: dict,
    remediation_status: str,
) -> Path:
    """
    Convenience function for generating
    an AeroDrift incident report.
    """

    generator = IncidentReportGenerator()

    return generator.generate(
        finding,
        remediation_status,
    )
    