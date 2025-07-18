# src/reporting/email_generator.py
import smtplib
import html
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger("market_aggregator.email")

class EmailGenerator:
    """
    Secure email generator with HTML templating and XSS protection
    """
    
    def __init__(self):
        # Get email configuration from environment
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD') 
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        
        # Validate email configuration
        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            missing = []
            if not self.sender_email: missing.append('SENDER_EMAIL')
            if not self.sender_password: missing.append('SENDER_PASSWORD')
            if not self.recipient_email: missing.append('RECIPIENT_EMAIL')
            
            error_msg = f"Missing email configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Email generator initialized successfully")

    def sanitize_html_content(self, text: str) -> str:
        """
        Sanitize text content to prevent XSS vulnerabilities
        
        Args:
            text: Raw text that might contain HTML
            
        Returns:
            HTML-escaped safe text
        """
        if not text:
            return ""
        
        # Escape HTML characters to prevent XSS
        return html.escape(text)

    def convert_markdown_to_html(self, text: str) -> str:
        """
        Convert markdown-style formatting to safe HTML
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            HTML-formatted text with XSS protection
        """
        if not text:
            return ""
        
        # First sanitize the input
        text = self.sanitize_html_content(text)
        
        # Now we can safely add HTML formatting since content is escaped
        # Bold text (escaped ** will become ** in HTML, then we make it bold)
        text = text.replace('**', '|||BOLD|||')  # Temporary marker
        
        # Split by our marker and reconstruct with proper HTML
        parts = text.split('|||BOLD|||')
        result = parts[0]
        
        for i in range(1, len(parts)):
            if i % 2 == 1:  # Odd indices should be bold
                result += '<strong>' + parts[i]
            else:  # Even indices close bold and continue
                result += '</strong>' + parts[i]
        
        # Clean up any unclosed bold tags
        bold_count = result.count('<strong>') - result.count('</strong>')
        if bold_count > 0:
            result += '</strong>' * bold_count
        
        # Convert headers (looking for lines that start with ## or ###)
        lines = result.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('###'):
                lines[i] = f'<h3>{line[3:].strip()}</h3>'
            elif line.startswith('##'):
                lines[i] = f'<h2>{line[2:].strip()}</h2>'
        
        result = '\n'.join(lines)
        
        # Convert line breaks to paragraphs
        paragraphs = result.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Don't wrap headers in paragraphs
                if para.startswith('<h') or para.startswith('<div'):
                    html_paragraphs.append(para)
                else:
                    # Replace single line breaks with <br> within paragraphs
                    para = para.replace('\n', '<br>')
                    html_paragraphs.append(f'<p>{para}</p>')
        
        return '\n'.join(html_paragraphs)

    def create_html_email(self, ai_analysis: str, ai_provider: str, 
                         article_count: int, successful_feeds: int, 
                         total_feeds: int) -> str:
        """
        Create a professional HTML email with the analysis
        
        Args:
            ai_analysis: The AI-generated analysis text
            ai_provider: Name of AI provider used
            article_count: Number of articles processed
            successful_feeds: Number of feeds that loaded successfully
            total_feeds: Total number of feeds attempted
            
        Returns:
            Complete HTML email content
        """
        # Convert the analysis to safe HTML
        analysis_html = self.convert_markdown_to_html(ai_analysis)
        
        # Create the HTML template
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 3px solid #2c3e50;
                }}
                .header h1 {{
                    color: #2c3e50;
                    margin: 0;
                    font-size: 28px;
                }}
                .meta {{
                    color: #666;
                    font-size: 14px;
                    text-align: center;
                    margin-top: 10px;
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .market-section {{
                    background-color: #f0f8ff;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    border-left: 4px solid #4169e1;
                }}
                .news-section {{
                    margin-top: 30px;
                }}
                h2 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                h3 {{
                    color: #2c3e50;
                    font-size: 18px;
                    margin-bottom: 10px;
                    margin-top: 25px;
                }}
                p {{
                    color: #444;
                    margin: 10px 0;
                }}
                .ticker {{
                    font-family: 'Courier New', monospace;
                    font-weight: bold;
                    color: #4169e1;
                    background-color: #f0f8ff;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
                .status-good {{ color: #27ae60; }}
                .status-warning {{ color: #f39c12; }}
                .status-error {{ color: #e74c3c; }}
                strong {{ color: #2c3e50; }}
                
                /* Mobile responsiveness */
                @media (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .container {{ padding: 15px; }}
                    .header h1 {{ font-size: 24px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Market & News Intelligence</h1>
                    <div class="meta">
                        <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}<br>
                        <strong>Analysis by:</strong> {html.escape(ai_provider)}<br>
                        <strong>Data Sources:</strong> {article_count:,} articles from {successful_feeds}/{total_feeds} feeds
                        {self._get_feed_status_indicator(successful_feeds, total_feeds)}
                    </div>
                </div>
                
                <div class="content">
                    {analysis_html}
                </div>
                
                <div class="footer">
                    <p><strong>🤖 AI Market Intelligence System</strong></p>
                    <p>Tracking: QQQ | SPY | UUP | IWM | GLD | COINBASE:BTCUSD | MP</p>
                    <p>This report was automatically generated with security-hardened data processing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template

    def _get_feed_status_indicator(self, successful: int, total: int) -> str:
        """Get a visual indicator for feed success rate"""
        if successful == total:
            return ' <span class="status-good">✅</span>'
        elif successful >= total * 0.8:  # 80% or better
            return ' <span class="status-warning">⚠️</span>'
        else:
            return ' <span class="status-error">❌</span>'

    def send_report(self, ai_analysis: str, ai_provider: str,
                   article_count: int, successful_feeds: int, 
                   total_feeds: int) -> bool:
        """
        Send the analysis report via email
        
        Args:
            ai_analysis: The AI-generated analysis
            ai_provider: Name of AI provider used
            article_count: Number of articles processed
            successful_feeds: Number of successful feed fetches
            total_feeds: Total feeds attempted
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            logger.info("Generating HTML email content...")
            
            # Create the HTML email content
            html_content = self.create_html_email(
                ai_analysis, ai_provider, article_count, 
                successful_feeds, total_feeds
            )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Market Intelligence Brief - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Create text version as fallback (strip HTML tags)
            text_content = re.sub(r'<[^>]+>', '', ai_analysis)
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send via Gmail SMTP
            logger.info("Connecting to Gmail SMTP server...")
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                
                # Don't log the actual password
                logger.info("Authenticating with Gmail...")
                server.login(self.sender_email, self.sender_password)
                
                logger.info(f"Sending email to {self.recipient_email}...")
                server.send_message(msg)
            
            logger.info("✅ Email sent successfully!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Email authentication failed - check credentials")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected email error: {e}")
            return False
