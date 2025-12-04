"""
Professional PDF Generator for BOQ Proposals
Follows construction industry best practices for BOQ documentation
"""
import io
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display


class ProfessionalBOQPDFGenerator:
    """Generate professional construction BOQ PDF proposals"""

    # Professional color scheme for construction industry
    PRIMARY_COLOR = colors.HexColor('#1e40af')  # Professional blue
    SECONDARY_COLOR = colors.HexColor('#059669')  # Success green
    ACCENT_COLOR = colors.HexColor('#d97706')  # Amber
    GRAY_DARK = colors.HexColor('#374151')
    GRAY_LIGHT = colors.HexColor('#f3f4f6')
    HEADER_BG = colors.HexColor('#1e3a8a')

    def __init__(self):
        """Initialize PDF generator with Hebrew font support"""
        self.styles = getSampleStyleSheet()
        self._setup_hebrew_fonts()
        self._create_custom_styles()

    def _setup_hebrew_fonts(self):
        """Register Hebrew fonts for PDF generation"""
        try:
            # Try to register common Hebrew fonts
            # For production, include a Hebrew TTF font in the assets
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/David.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('HebrewFont', font_path))
                    pdfmetrics.registerFont(TTFont('HebrewFont-Bold', font_path))
                    break
        except Exception as e:
            print(f"Warning: Could not register Hebrew font: {e}")
            # Fallback to default fonts

    def _create_custom_styles(self):
        """Create custom paragraph styles for the document"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='HebrewFont-Bold'
        ))

        # Heading styles
        self.styles.add(ParagraphStyle(
            name='HebrewHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_RIGHT,
            fontName='HebrewFont-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='HebrewHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.GRAY_DARK,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_RIGHT,
            fontName='HebrewFont-Bold'
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='HebrewBody',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            fontName='HebrewFont',
            leading=14
        ))

        # Chapter heading
        self.styles.add(ParagraphStyle(
            name='ChapterHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.white,
            backColor=self.HEADER_BG,
            spaceAfter=6,
            spaceBefore=6,
            alignment=TA_RIGHT,
            fontName='HebrewFont-Bold',
            leftIndent=10,
            rightIndent=10
        ))

    def _format_hebrew(self, text: str) -> str:
        """Format Hebrew text for proper RTL display in PDF"""
        if not text:
            return ""
        try:
            reshaped_text = reshape(text)
            return get_display(reshaped_text)
        except:
            return text

    def _format_currency(self, amount: float) -> str:
        """Format currency with Israeli formatting"""
        return f"₪ {amount:,.2f}"

    def _create_header_footer(self, canvas, doc, project_name: str, logo_path: Optional[str] = None):
        """Draw header and footer on each page"""
        canvas.saveState()

        # Header
        if logo_path and os.path.exists(logo_path):
            try:
                canvas.drawImage(logo_path, 2*cm, A4[1] - 3*cm, width=3*cm, height=2*cm,
                               preserveAspectRatio=True, mask='auto')
            except:
                pass

        # Project name in header
        canvas.setFont('HebrewFont-Bold', 10)
        canvas.setFillColor(self.PRIMARY_COLOR)
        header_text = self._format_hebrew(f"כתב כמויות - {project_name}")
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 2*cm, header_text)

        # Header line
        canvas.setStrokeColor(self.PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(2*cm, A4[1] - 3.5*cm, A4[0] - 2*cm, A4[1] - 3.5*cm)

        # Footer
        canvas.setFont('HebrewFont', 8)
        canvas.setFillColor(self.GRAY_DARK)

        # Page number
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(A4[0] / 2, 1.5*cm, self._format_hebrew(f"עמוד {page_num}"))

        # Date
        date_str = datetime.now().strftime("%d/%m/%Y")
        canvas.drawRightString(A4[0] - 2*cm, 1.5*cm, self._format_hebrew(f"תאריך: {date_str}"))

        # Footer line
        canvas.setStrokeColor(self.GRAY_DARK)
        canvas.setLineWidth(0.5)
        canvas.line(2*cm, 2*cm, A4[0] - 2*cm, 2*cm)

        canvas.restoreState()

    def _create_cover_page(self, project_name: str, logo_path: Optional[str] = None) -> List:
        """Create professional cover page"""
        story = []

        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=8*cm, height=5*cm)
                story.append(Spacer(1, 3*cm))
                story.append(img)
                story.append(Spacer(1, 1*cm))
            except Exception as e:
                print(f"Could not load logo: {e}")
                story.append(Spacer(1, 5*cm))
        else:
            story.append(Spacer(1, 5*cm))

        # Main title
        title = Paragraph(
            self._format_hebrew("כתב כמויות מפורט"),
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 1*cm))

        # Project name
        project_title = Paragraph(
            f'<font size="18" color="#059669"><b>{self._format_hebrew(project_name)}</b></font>',
            self.styles['CustomTitle']
        )
        story.append(project_title)
        story.append(Spacer(1, 2*cm))

        # Professional box with project details
        details_data = [
            [self._format_hebrew("תאריך הצעה:"), datetime.now().strftime("%d/%m/%Y")],
            [self._format_hebrew("מספר הצעה:"), f"BOQ-{datetime.now().strftime('%Y%m%d-%H%M')}"],
            [self._format_hebrew("תוקף ההצעה:"), self._format_hebrew("30 יום")],
        ]

        details_table = Table(details_data, colWidths=[6*cm, 8*cm])
        details_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 11),
            ('FONTNAME', (0, 0), (0, -1), 'HebrewFont-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.GRAY_DARK),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), self.GRAY_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [self.GRAY_LIGHT, colors.white]),
        ]))

        story.append(details_table)
        story.append(Spacer(1, 3*cm))

        # Professional statement
        statement = Paragraph(
            self._format_hebrew(
                "הצעת מחיר זו הוכנה בקפידה רבה ומבוססת על תכניות ומפרטים שהתקבלו. "
                "ההצעה כוללת את כל העבודות, החומרים והציוד הדרושים לביצוע הפרויקט. "
                "המחירים המפורטים בכתב הכמויות מבוססים על מחירון דקל ותקן ישראלי."
            ),
            self.styles['HebrewBody']
        )
        story.append(statement)

        # Page break after cover
        story.append(PageBreak())

        return story

    def _create_executive_summary(self, boq_data: Dict[str, Any]) -> List:
        """Create executive summary page"""
        story = []

        # Title
        title = Paragraph(
            self._format_hebrew("סיכום מנהלים"),
            self.styles['HebrewHeading1']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*cm))

        # Summary table - RTL order
        summary = boq_data.get('summary', {})
        summary_data = [
            [self._format_hebrew("סכום"), self._format_hebrew("פרט")],
            [self._format_currency(summary.get('subtotal', 0)), self._format_hebrew("סכום ביניים")],
            [self._format_currency(summary.get('vat_amount', 0)),
             self._format_hebrew(f"מע\"מ ({int(summary.get('vat_rate', 0.17) * 100)}%)")],
            [self._format_currency(summary.get('grand_total', 0)), self._format_hebrew("סה\"כ כולל מע\"מ")],
        ]

        summary_table = Table(summary_data, colWidths=[6*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 12),
            ('FONTNAME', (0, 0), (-1, 0), 'HebrewFont-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'HebrewFont-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), self.SECONDARY_COLOR),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
        ]))

        story.append(summary_table)
        story.append(Spacer(1, 1*cm))

        # Project statistics
        stats_title = Paragraph(
            self._format_hebrew("נתוני הפרויקט"),
            self.styles['HebrewHeading2']
        )
        story.append(stats_title)
        story.append(Spacer(1, 0.3*cm))

        stats_data = [
            [str(len(boq_data.get('chapters', []))), self._format_hebrew("מספר פרקים")],
            [str(summary.get('total_items', 0)), self._format_hebrew("מספר פריטים")],
            [str(summary.get('total_files', 0)), self._format_hebrew("קבצי מקור")],
        ]

        stats_table = Table(stats_data, colWidths=[4*cm, 12*cm])
        stats_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 10),
            ('FONTNAME', (1, 0), (1, -1), 'HebrewFont-Bold'),  # Labels in column 1 are bold
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), self.GRAY_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(stats_table)
        story.append(PageBreak())

        return story

    def _create_chapter_table(self, chapter: Dict[str, Any]) -> List:
        """Create table for a single chapter"""
        story = []

        # Chapter header
        chapter_title = Paragraph(
            self._format_hebrew(f"פרק {chapter['chapter_code']}: {chapter['chapter_name_he']}"),
            self.styles['ChapterHeading']
        )
        story.append(chapter_title)
        story.append(Spacer(1, 0.3*cm))

        # Table header - RTL order (rightmost column first)
        table_data = [[
            self._format_hebrew("סה\"כ"),
            self._format_hebrew("מחיר יחידה"),
            self._format_hebrew("יחידה"),
            self._format_hebrew("כמות"),
            self._format_hebrew("תיאור"),
            self._format_hebrew("קוד"),
        ]]

        # Table rows - RTL order
        for item in chapter.get('items', []):
            # Wrap description in Paragraph for proper text wrapping
            desc_style = ParagraphStyle(
                'TableCell',
                fontName='HebrewFont',
                fontSize=7,
                alignment=TA_RIGHT,
                leading=9,
            )
            description_para = Paragraph(
                self._format_hebrew(item.get('description_he', '')),
                desc_style
            )

            table_data.append([
                self._format_currency(item.get('total_price', 0)),
                self._format_currency(item.get('unit_price', 0)),
                self._format_hebrew(item.get('unit', '')),
                f"{item.get('quantity', 0):,.2f}",
                description_para,  # Use Paragraph for automatic wrapping
                item.get('item_code', ''),
            ])

        # Chapter total row - RTL order
        table_data.append([
            self._format_currency(chapter.get('chapter_total', 0)),
            "",
            "",
            "",
            self._format_hebrew("סה\"כ פרק"),
            "",
        ])

        # Create table - RTL column widths
        # Order: Total, Unit Price, Unit, Quantity, Description, Code
        col_widths = [3*cm, 2.8*cm, 1.5*cm, 2*cm, 5.5*cm, 2*cm]
        chapter_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Table styling - RTL aligned
        table_style = [
            # Header row
            ('FONT', (0, 0), (-1, 0), 'HebrewFont-Bold', 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows - RTL order: Total, Unit Price, Unit, Quantity, Description, Code
            ('FONT', (0, 1), (-1, -2), 'HebrewFont', 8),
            ('ALIGN', (0, 1), (1, -2), 'RIGHT'),   # Total & Unit Price
            ('ALIGN', (2, 1), (2, -2), 'CENTER'),  # Unit
            ('ALIGN', (3, 1), (3, -2), 'RIGHT'),   # Quantity
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),   # Description
            ('ALIGN', (5, 1), (5, -2), 'CENTER'),  # Item code

            # Total row
            ('FONT', (0, -1), (-1, -1), 'HebrewFont-Bold', 10),
            ('BACKGROUND', (0, -1), (-1, -1), self.SECONDARY_COLOR),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),

            # General styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.GRAY_LIGHT]),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Header row: middle align
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),  # Data rows: top align for multi-line text
        ]

        chapter_table.setStyle(TableStyle(table_style))

        # Wrap in KeepTogether to avoid splitting chapter header from table
        story.append(KeepTogether([chapter_table]))
        story.append(Spacer(1, 0.8*cm))

        return story

    def _create_terms_and_conditions(self) -> List:
        """Create terms and conditions page"""
        story = []

        story.append(PageBreak())

        title = Paragraph(
            self._format_hebrew("תנאים והערות"),
            self.styles['HebrewHeading1']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*cm))

        terms = [
            "המחירים בהצעה זו תקפים ל-30 יום מתאריך ההצעה.",
            "המחירים מבוססים על מחירון דקל העדכני ביותר.",
            "ההצעה כוללת עבודה, חומרים וציוד הדרושים לביצוע העבודות.",
            "ההצעה אינה כוללת עבודות עפר והכנת שטח, אלא אם צוין אחרת.",
            "כל שינוי בתכניות או במפרט עלול לגרום לשינוי במחירים.",
            "תשלום יבוצע לפי התקדמות העבודה בפועל.",
            "זמני אספקה וביצוע יתואמו עם הלקוח.",
            "אחריות על העבודות והחומרים לפי התקן הישראלי.",
        ]

        for i, term in enumerate(terms, 1):
            term_text = Paragraph(
                f"{i}. {self._format_hebrew(term)}",
                self.styles['HebrewBody']
            )
            story.append(term_text)
            story.append(Spacer(1, 0.3*cm))

        story.append(Spacer(1, 2*cm))

        # Signature section
        signature_data = [
            [self._format_hebrew("חתימת המציע:"), "_" * 30],
            [self._format_hebrew("תאריך:"), "_" * 30],
        ]

        signature_table = Table(signature_data, colWidths=[4*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(signature_table)

        return story

    def generate_pdf(
        self,
        boq_data: Dict[str, Any],
        output_path: Optional[str] = None,
        logo_path: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> io.BytesIO:
        """
        Generate professional BOQ PDF

        Args:
            boq_data: BOQ data dictionary
            output_path: Optional file path to save PDF
            logo_path: Optional path to company logo image
            company_name: Optional company name

        Returns:
            BytesIO buffer containing the PDF
        """
        # Create buffer
        buffer = io.BytesIO()

        # Create document
        if output_path:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=4*cm,
                bottomMargin=2.5*cm
            )
        else:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=4*cm,
                bottomMargin=2.5*cm
            )

        # Build document content
        story = []

        # Cover page
        project_name = boq_data.get('project_name', 'פרויקט ללא שם')
        story.extend(self._create_cover_page(project_name, logo_path))

        # Executive summary
        story.extend(self._create_executive_summary(boq_data))

        # Chapters
        for chapter in boq_data.get('chapters', []):
            story.extend(self._create_chapter_table(chapter))

        # Terms and conditions
        story.extend(self._create_terms_and_conditions())

        # Build PDF with header/footer
        doc.build(
            story,
            onFirstPage=lambda c, d: self._create_header_footer(c, d, project_name, logo_path),
            onLaterPages=lambda c, d: self._create_header_footer(c, d, project_name, logo_path)
        )

        if not output_path:
            buffer.seek(0)
            return buffer

        return buffer


def generate_boq_pdf(
    boq_data: Dict[str, Any],
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None
) -> io.BytesIO:
    """
    Generate professional BOQ PDF

    Args:
        boq_data: BOQ data dictionary
        logo_path: Optional path to company logo
        company_name: Optional company name

    Returns:
        BytesIO buffer with PDF content
    """
    generator = ProfessionalBOQPDFGenerator()
    return generator.generate_pdf(boq_data, logo_path=logo_path, company_name=company_name)
