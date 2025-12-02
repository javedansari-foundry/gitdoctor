"""
Notification modules for GitDoctor.

Supports sending notifications via Slack, Microsoft Teams, and Email when delta discovery completes.
"""

import logging
import json
from typing import Optional, Dict, Any
from pathlib import Path

import requests

from .models import DeltaSummary, DeltaResult


logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Send notifications to Slack webhook.
    
    Requires a Slack webhook URL configured in environment or config.
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL (from Slack app configuration)
        """
        self.webhook_url = webhook_url
    
    def send_delta_notification(
        self,
        summary: DeltaSummary,
        output_file: Optional[str] = None,
        base_ref: str = "",
        target_ref: str = ""
    ) -> bool:
        """
        Send delta discovery summary to Slack.
        
        Args:
            summary: DeltaSummary object with statistics
            output_file: Path to generated report file (optional)
            base_ref: Base reference name
            target_ref: Target reference name
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Build Slack message
            message = self._build_slack_message(summary, output_file, base_ref, target_ref)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Slack notification sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Slack notification: {e}")
            return False
    
    def _build_slack_message(
        self,
        summary: DeltaSummary,
        output_file: Optional[str],
        base_ref: str,
        target_ref: str
    ) -> Dict[str, Any]:
        """Build Slack message payload."""
        
        # Determine color based on results
        if summary.projects_with_errors > 0:
            color = "#ff0000"  # Red
        elif summary.total_commits > 0:
            color = "#36a64f"  # Green
        else:
            color = "#ffa500"  # Orange
        
        # Build fields
        fields = [
            {
                "title": "Base Reference",
                "value": summary.base_ref,
                "short": True
            },
            {
                "title": "Target Reference",
                "value": summary.target_ref,
                "short": True
            },
            {
                "title": "Projects Searched",
                "value": str(summary.total_projects),
                "short": True
            },
            {
                "title": "Projects with Changes",
                "value": str(summary.projects_with_changes),
                "short": True
            },
            {
                "title": "Total Commits",
                "value": str(summary.total_commits),
                "short": True
            },
            {
                "title": "Files Changed",
                "value": str(summary.total_files_changed),
                "short": True
            }
        ]
        
        if summary.projects_with_errors > 0:
            fields.append({
                "title": "⚠️ Projects with Errors",
                "value": str(summary.projects_with_errors),
                "short": True
            })
        
        # Build attachment
        attachment = {
            "color": color,
            "title": "🔍 GitDoctor Delta Discovery Complete",
            "fields": fields,
            "footer": "GitDoctor",
            "ts": int(summary.__dict__.get('timestamp', 0)) if hasattr(summary, 'timestamp') else None
        }
        
        if output_file:
            attachment["text"] = f"📄 Report generated: `{Path(output_file).name}`"
        
        # Build message
        message = {
            "text": f"Delta discovery completed: {base_ref} → {target_ref}",
            "attachments": [attachment]
        }
        
        return message


class TeamsNotifier:
    """
    Send notifications to Microsoft Teams webhook.
    
    Requires a Teams webhook URL configured in a Teams channel.
    """
    
    def __init__(self, webhook_url: str):
        """
        Initialize Teams notifier.
        
        Args:
            webhook_url: Teams webhook URL (from Teams channel connector)
        """
        self.webhook_url = webhook_url
    
    def send_delta_notification(
        self,
        summary: DeltaSummary,
        output_file: Optional[str] = None,
        base_ref: str = "",
        target_ref: str = ""
    ) -> bool:
        """
        Send delta discovery summary to Microsoft Teams.
        
        Args:
            summary: DeltaSummary object with statistics
            output_file: Path to generated report file (optional)
            base_ref: Base reference name
            target_ref: Target reference name
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Build Teams Adaptive Card message
            message = self._build_teams_message(summary, output_file, base_ref, target_ref)
            
            # Send to Teams
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Teams notification sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Teams notification: {e}")
            return False
    
    def _build_teams_message(
        self,
        summary: DeltaSummary,
        output_file: Optional[str],
        base_ref: str,
        target_ref: str
    ) -> Dict[str, Any]:
        """Build Teams Adaptive Card message payload."""
        
        # Determine theme color based on results
        if summary.projects_with_errors > 0:
            theme_color = "FF0000"  # Red
        elif summary.total_commits > 0:
            theme_color = "00FF00"  # Green
        else:
            theme_color = "FFA500"  # Orange
        
        # Build facts section
        facts = [
            {"name": "Base Reference", "value": summary.base_ref},
            {"name": "Target Reference", "value": summary.target_ref},
            {"name": "Projects Searched", "value": str(summary.total_projects)},
            {"name": "Projects with Changes", "value": str(summary.projects_with_changes)},
            {"name": "Total Commits", "value": str(summary.total_commits)},
            {"name": "Files Changed", "value": str(summary.total_files_changed)}
        ]
        
        if summary.projects_with_errors > 0:
            facts.append({
                "name": "⚠️ Projects with Errors",
                "value": str(summary.projects_with_errors)
            })
        
        # Build Adaptive Card
        card = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"GitDoctor Delta Discovery: {base_ref} → {target_ref}",
            "themeColor": theme_color,
            "title": "🔍 GitDoctor Delta Discovery Complete",
            "sections": [
                {
                    "activityTitle": f"Delta discovery completed: {base_ref} → {target_ref}",
                    "facts": facts
                }
            ]
        }
        
        if output_file:
            card["sections"][0]["text"] = f"📄 Report generated: **{Path(output_file).name}**"
        
        return card


class EmailNotifier:
    """
    Send notifications via email using SMTP.
    
    Requires SMTP server configuration.
    """
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: list
    ):
        """
        Initialize email notifier.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: Sender email address
            to_emails: List of recipient email addresses
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    def send_delta_notification(
        self,
        summary: DeltaSummary,
        output_file: Optional[str] = None,
        subject_prefix: str = "GitDoctor Delta Report"
    ) -> bool:
        """
        Send delta discovery summary via email.
        
        Args:
            summary: DeltaSummary object with statistics
            output_file: Path to generated report file (optional)
            subject_prefix: Email subject prefix
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Build email
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(self.to_emails)
            msg['Subject'] = f"{subject_prefix}: {summary.base_ref} → {summary.target_ref}"
            
            # Build email body
            body = self._build_email_body(summary, output_file)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach file if provided
            if output_file and Path(output_file).exists():
                from email.mime.base import MIMEBase
                from email import encoders
                
                with open(output_file, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {Path(output_file).name}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {', '.join(self.to_emails)}")
            return True
            
        except ImportError:
            logger.error("Email functionality requires Python's built-in smtplib (should be available)")
            return False
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _build_email_body(self, summary: DeltaSummary, output_file: Optional[str]) -> str:
        """Build HTML email body."""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background: #667eea; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .stat {{ margin: 10px 0; }}
                .stat-label {{ font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #667eea; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 GitDoctor Delta Discovery Report</h1>
            </div>
            <div class="content">
                <h2>Summary</h2>
                <div class="stat">
                    <span class="stat-label">Base Reference:</span> {summary.base_ref}
                </div>
                <div class="stat">
                    <span class="stat-label">Target Reference:</span> {summary.target_ref}
                </div>
                <div class="stat">
                    <span class="stat-label">Projects Searched:</span> {summary.total_projects}
                </div>
                <div class="stat">
                    <span class="stat-label">Projects with Changes:</span> {summary.projects_with_changes}
                </div>
                <div class="stat">
                    <span class="stat-label">Total Commits:</span> {summary.total_commits}
                </div>
                <div class="stat">
                    <span class="stat-label">Files Changed:</span> {summary.total_files_changed}
                </div>
                {f'<p><strong>Report file:</strong> {Path(output_file).name}</p>' if output_file else ''}
                <p>Please see the attached report for detailed information.</p>
            </div>
        </body>
        </html>
        """


def create_slack_notifier(webhook_url: str) -> Optional[SlackNotifier]:
    """
    Create a Slack notifier if webhook URL is provided.
    
    Args:
        webhook_url: Slack webhook URL (can be empty/None)
        
    Returns:
        SlackNotifier instance or None
    """
    if webhook_url and webhook_url.strip():
        return SlackNotifier(webhook_url.strip())
    return None


def create_teams_notifier(webhook_url: str) -> Optional[TeamsNotifier]:
    """
    Create a Teams notifier if webhook URL is provided.
    
    Args:
        webhook_url: Teams webhook URL (can be empty/None)
        
    Returns:
        TeamsNotifier instance or None
    """
    if webhook_url and webhook_url.strip():
        return TeamsNotifier(webhook_url.strip())
    return None


def create_email_notifier(
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    from_email: Optional[str] = None,
    to_emails: Optional[list] = None
) -> Optional[EmailNotifier]:
    """
    Create an email notifier if all required parameters are provided.
    
    Args:
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        from_email: Sender email
        to_emails: List of recipient emails
        
    Returns:
        EmailNotifier instance or None
    """
    if all([smtp_server, smtp_port, username, password, from_email, to_emails]):
        return EmailNotifier(
            smtp_server, smtp_port, username, password, from_email, to_emails
        )
    return None

