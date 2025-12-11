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

    def _create_cover_page(self, project_name: str, logo_path: Optional[str] = None, boq_data: Optional[Dict] = None) -> List:
        """
        Create מוריה-style professional cover page.
        Includes tender info box and project details.
        """
        story = []

        # Logo
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=6*cm, height=3*cm)
                story.append(Spacer(1, 1*cm))
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            except Exception as e:
                print(f"Could not load logo: {e}")
                story.append(Spacer(1, 2*cm))
        else:
            story.append(Spacer(1, 2*cm))

        # Main title - מוריה style
        title = Paragraph(
            self._format_hebrew("כתב כמויות למכרז"),
            ParagraphStyle(
                'MoriahTitle',
                parent=self.styles['Heading1'],
                fontSize=22,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='HebrewFont-Bold'
            )
        )
        story.append(title)

        # Project name
        project_title = Paragraph(
            self._format_hebrew(project_name),
            ParagraphStyle(
                'ProjectTitle',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=self.GRAY_DARK,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='HebrewFont-Bold'
            )
        )
        story.append(project_title)

        # מוריה-style info box - RTL table
        # Columns: Value | Label (displayed right-to-left)
        tender_number = f"BOQ-{datetime.now().strftime('%Y%m%d')}"
        date_str = datetime.now().strftime("%d/%m/%Y")

        # Calculate estimate if available
        estimate = 0
        if boq_data:
            # Try non-hierarchical format first (summary.subtotal)
            summary = boq_data.get('summary', {})
            if summary and summary.get('subtotal'):
                estimate = summary.get('subtotal', 0)
            # Fallback to hierarchical format (sub_documents)
            elif boq_data.get('sub_documents'):
                for sub_doc in boq_data.get('sub_documents', []):
                    estimate += sub_doc.get('cached_total', 0)
            # Fallback to calculating from chapters
            elif boq_data.get('chapters'):
                for chapter in boq_data.get('chapters', []):
                    estimate += chapter.get('chapter_total', 0)

        info_data = [
            [tender_number, self._format_hebrew("מכרז מספר:")],
            [date_str, self._format_hebrew("תאריך:")],
            [f"{estimate:,.2f}", self._format_hebrew("אומדן (ללא מע\"מ):")],
            [self._format_hebrew("30 יום"), self._format_hebrew("תוקף ההצעה:")],
        ]

        info_table = Table(info_data, colWidths=[8*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 11),
            ('FONTNAME', (1, 0), (1, -1), 'HebrewFont-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.GRAY_DARK),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),   # Values
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Labels
            ('BACKGROUND', (0, 0), (-1, -1), self.GRAY_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 2, self.PRIMARY_COLOR),
        ]))

        story.append(info_table)
        story.append(Spacer(1, 2*cm))

        # Professional statement
        statement = Paragraph(
            self._format_hebrew(
                "כתב כמויות זה הוכן בהתאם לתקן הישראלי ומחירון דקל. "
                "הכמויות והמחירים מבוססים על תכניות ומפרטים שהתקבלו. "
                "ההצעה כוללת את כל העבודות, החומרים והציוד הדרושים לביצוע הפרויקט."
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
        story.extend(self._create_cover_page(project_name, logo_path, boq_data))

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


    def _create_sub_document_header(self, sub_doc: Dict[str, Any]) -> List:
        """Create header for a sub-document (תת כתב)"""
        story = []

        # Sub-document heading with full-width background
        sub_doc_title = Paragraph(
            self._format_hebrew(f"תת כתב {sub_doc['code']}: {sub_doc['name_he']}"),
            ParagraphStyle(
                'SubDocumentHeading',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.white,
                backColor=self.PRIMARY_COLOR,
                spaceAfter=12,
                spaceBefore=12,
                alignment=TA_RIGHT,
                fontName='HebrewFont-Bold',
                leftIndent=10,
                rightIndent=10
            )
        )
        story.append(sub_doc_title)
        story.append(Spacer(1, 0.5*cm))

        return story

    def _create_chapter_header(self, chapter: Dict[str, Any]) -> List:
        """Create header for a chapter (פרק)"""
        story = []

        chapter_title = Paragraph(
            self._format_hebrew(f"פרק {chapter['code']}: {chapter['name_he']}"),
            ParagraphStyle(
                'ChapterHeading2',
                parent=self.styles['Heading2'],
                fontSize=13,
                textColor=colors.white,
                backColor=self.HEADER_BG,
                spaceAfter=8,
                spaceBefore=8,
                alignment=TA_RIGHT,
                fontName='HebrewFont-Bold',
                leftIndent=20,
                rightIndent=10
            )
        )
        story.append(chapter_title)
        story.append(Spacer(1, 0.3*cm))

        return story

    def _create_sub_chapter_table(self, sub_chapter: Dict[str, Any], sub_doc_code: str = "1", chapter_code: str = "1") -> List:
        """
        Create table for a sub-chapter (תת פרק) with its items.
        Follows מוריה professional BOQ format.

        Column order (RTL - right to left as displayed):
        מספר סעיף | תאור הסעיף | יח' | כמות | מחיר | סה"כ
        """
        story = []

        # Sub-chapter header - מוריה format: תת פרק: X.Y [name]
        sc_code = sub_chapter.get('code', '1')
        sc_title = Paragraph(
            self._format_hebrew(f"תת פרק: {chapter_code}.{sc_code}  {sub_chapter['name_he']}"),
            ParagraphStyle(
                'SubChapterHeading',
                parent=self.styles['Heading3'],
                fontSize=10,
                textColor=self.GRAY_DARK,
                spaceAfter=4,
                spaceBefore=8,
                alignment=TA_RIGHT,
                fontName='HebrewFont-Bold',
            )
        )
        story.append(sc_title)

        items = sub_chapter.get('items', [])
        if not items:
            story.append(Spacer(1, 0.3*cm))
            return story

        # Table header - מוריה format (RTL display order)
        # Visual order: מספר סעיף | תאור הסעיף | יח' | כמות | מחיר | סה"כ
        table_data = [[
            self._format_hebrew("סה\"כ"),
            self._format_hebrew("מחיר"),
            self._format_hebrew("כמות"),
            self._format_hebrew("יח'"),
            self._format_hebrew("תאור הסעיף"),
            self._format_hebrew("מספר סעיף"),
        ]]

        # Table rows - מוריה item numbering format: X.Y.Z.NNNN
        for idx, item in enumerate(items, 1):
            # Generate מוריה-style item code: תת_כתב.פרק.תת_פרק.sequence
            item_sequence = f"{idx:04d}"  # 0010, 0020, etc.
            moriah_item_code = f"{sub_doc_code}.{chapter_code}.{sc_code}.{item_sequence}"

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

            # מוריה format row order (for RTL display)
            table_data.append([
                f"{item.get('total_price', 0):,.2f}",
                f"{item.get('unit_price', 0):,.2f}",
                f"{item.get('quantity', 0):,.2f}",
                self._format_hebrew(item.get('unit', '')),
                description_para,
                moriah_item_code,
            ])

        # Sub-chapter total row - מוריה format
        sc_full_code = f"{chapter_code}.{sc_code}"
        table_data.append([
            f"{sub_chapter.get('cached_total', 0):,.2f}",
            "",
            "",
            "",
            self._format_hebrew(f"סה\"כ לתת פרק: {sc_full_code}  {sub_chapter['name_he']}"),
            "",
        ])

        # Create table - מוריה column widths
        # סה"כ | מחיר | כמות | יח' | תאור הסעיף | מספר סעיף
        col_widths = [2.5*cm, 2.2*cm, 2*cm, 1.3*cm, 6*cm, 2.8*cm]
        sc_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style = [
            # Header row
            ('FONT', (0, 0), (-1, 0), 'HebrewFont-Bold', 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.GRAY_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('FONT', (0, 1), (-1, -2), 'HebrewFont', 7),
            ('ALIGN', (0, 1), (2, -2), 'RIGHT'),   # סה"כ, מחיר, כמות - right align
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),  # יח' - center
            ('ALIGN', (4, 1), (4, -2), 'RIGHT'),   # תאור - right align
            ('ALIGN', (5, 1), (5, -2), 'LEFT'),    # מספר סעיף - left (appears right in RTL)

            # Total row
            ('FONT', (0, -1), (-1, -1), 'HebrewFont-Bold', 8),
            ('BACKGROUND', (0, -1), (-1, -1), self.GRAY_LIGHT),
            ('TEXTCOLOR', (0, -1), (-1, -1), self.GRAY_DARK),
            ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),

            # General styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.GRAY_LIGHT]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]

        sc_table.setStyle(TableStyle(table_style))
        story.append(sc_table)
        story.append(Spacer(1, 0.3*cm))

        return story

    def _create_hierarchical_summary(self, boq_data: Dict[str, Any]) -> List:
        """
        Create מוריה-style "ריכוז למכרז" summary page.
        Shows complete hierarchy with subtotals at each level.
        """
        story = []

        # Title - מוריה style
        title = Paragraph(
            self._format_hebrew("ריכוז למכרז"),
            ParagraphStyle(
                'SummaryTitle',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=self.GRAY_DARK,
                spaceAfter=15,
                alignment=TA_CENTER,
                fontName='HebrewFont-Bold'
            )
        )
        story.append(title)

        # Build hierarchy summary table - מוריה format
        # Columns: סה"כ | נושא
        summary_data = []

        grand_total = 0

        for sub_doc in boq_data.get('sub_documents', []):
            sub_doc_code = sub_doc.get('code', '1')
            sub_doc_name = sub_doc.get('name_he', '')
            sub_doc_total = 0

            # תת כתב header row
            summary_data.append([
                "",
                self._format_hebrew(f"תת כתב: {sub_doc_code}  {sub_doc_name}")
            ])

            for chapter in sub_doc.get('chapters', []):
                ch_code = chapter.get('code', '1')
                ch_name = chapter.get('name_he', '')
                chapter_total = 0

                for sub_chapter in chapter.get('sub_chapters', []):
                    sc_code = sub_chapter.get('code', '1')
                    sc_name = sub_chapter.get('name_he', '')
                    sc_total = sub_chapter.get('cached_total', 0)
                    chapter_total += sc_total

                    # תת פרק row
                    summary_data.append([
                        f"{sc_total:,.2f}",
                        self._format_hebrew(f"תת פרק: {ch_code}.{sc_code}  {sc_name}")
                    ])

                # סה"כ לפרק row
                sub_doc_total += chapter_total
                summary_data.append([
                    f"{chapter_total:,.2f}",
                    self._format_hebrew(f"סה\"כ לפרק: {ch_code}  {ch_name}")
                ])

            # סה"כ לתת כתב row
            grand_total += sub_doc_total
            summary_data.append([
                f"{sub_doc_total:,.2f}",
                self._format_hebrew(f"סה\"כ לתת כתב: {sub_doc_code}  {sub_doc_name}")
            ])

        # סה"כ לכל כתב הכמויות row
        summary_data.append([
            f"{grand_total:,.2f}",
            self._format_hebrew("סה\"כ לכל כתב הכמויות:")
        ])

        # Create summary table
        col_widths = [4*cm, 12.8*cm]
        summary_table = Table(summary_data, colWidths=col_widths)

        # Style the table - identify special rows
        table_style = [
            ('FONT', (0, 0), (-1, -1), 'HebrewFont', 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Amount column
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Description column
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Style specific rows based on content
        for i, row in enumerate(summary_data):
            row_text = row[1] if len(row) > 1 else ""
            if isinstance(row_text, str):
                if "תת כתב:" in row_text and "סה\"כ" not in row_text:
                    # תת כתב header - bold, blue background
                    table_style.append(('BACKGROUND', (0, i), (-1, i), self.PRIMARY_COLOR))
                    table_style.append(('TEXTCOLOR', (0, i), (-1, i), colors.white))
                    table_style.append(('FONTNAME', (0, i), (-1, i), 'HebrewFont-Bold'))
                elif "סה\"כ לפרק:" in row_text:
                    # Chapter total - bold
                    table_style.append(('FONTNAME', (0, i), (-1, i), 'HebrewFont-Bold'))
                    table_style.append(('BACKGROUND', (0, i), (-1, i), self.GRAY_LIGHT))
                elif "סה\"כ לתת כתב:" in row_text:
                    # Sub-document total - bold, darker
                    table_style.append(('FONTNAME', (0, i), (-1, i), 'HebrewFont-Bold'))
                    table_style.append(('BACKGROUND', (0, i), (-1, i), self.HEADER_BG))
                    table_style.append(('TEXTCOLOR', (0, i), (-1, i), colors.white))
                elif "סה\"כ לכל כתב הכמויות" in row_text:
                    # Grand total - bold, green
                    table_style.append(('FONTNAME', (0, i), (-1, i), 'HebrewFont-Bold'))
                    table_style.append(('FONTSIZE', (0, i), (-1, i), 11))
                    table_style.append(('BACKGROUND', (0, i), (-1, i), self.SECONDARY_COLOR))
                    table_style.append(('TEXTCOLOR', (0, i), (-1, i), colors.white))

        summary_table.setStyle(TableStyle(table_style))
        story.append(summary_table)
        story.append(PageBreak())

        return story

    def generate_hierarchical_pdf(
        self,
        boq_data: Dict[str, Any],
        output_path: Optional[str] = None,
        logo_path: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> io.BytesIO:
        """
        Generate professional hierarchical BOQ PDF with 4-level structure.

        Args:
            boq_data: Hierarchical BOQ data from build_hierarchy_response
            output_path: Optional file path to save PDF
            logo_path: Optional path to company logo image
            company_name: Optional company name

        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = io.BytesIO()

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

        story = []

        # Cover page - מוריה style with estimate
        project_name = boq_data.get('project_name', 'פרויקט ללא שם')
        story.extend(self._create_cover_page(project_name, logo_path, boq_data))

        # ריכוז למכרז - Hierarchical summary (מוריה style)
        story.extend(self._create_hierarchical_summary(boq_data))

        # Hierarchical content: Sub-Documents -> Chapters -> Sub-Chapters -> Items
        # מוריה format with proper codes at each level
        for sub_doc in boq_data.get('sub_documents', []):
            sub_doc_code = sub_doc.get('code', '1')
            story.extend(self._create_sub_document_header(sub_doc))

            sub_doc_total = 0

            for chapter in sub_doc.get('chapters', []):
                chapter_code = chapter.get('code', '1')
                story.extend(self._create_chapter_header(chapter))

                # Chapter total tracker
                chapter_total = 0

                for sub_chapter in chapter.get('sub_chapters', []):
                    # Pass codes for מוריה-style item numbering
                    story.extend(self._create_sub_chapter_table(
                        sub_chapter,
                        sub_doc_code=sub_doc_code,
                        chapter_code=chapter_code
                    ))
                    chapter_total += sub_chapter.get('cached_total', 0)

                # Chapter total row - מוריה format
                ch_total = Paragraph(
                    self._format_hebrew(f"סה\"כ לפרק: {chapter_code}  {chapter.get('name_he', '')}  {chapter_total:,.2f}"),
                    ParagraphStyle(
                        'ChapterTotal',
                        fontName='HebrewFont-Bold',
                        fontSize=10,
                        textColor=self.GRAY_DARK,
                        backColor=self.GRAY_LIGHT,
                        alignment=TA_RIGHT,
                        spaceAfter=10,
                        spaceBefore=5,
                        leftIndent=5,
                        rightIndent=5
                    )
                )
                story.append(ch_total)
                story.append(Spacer(1, 0.5*cm))

                sub_doc_total += chapter_total

            # Sub-document total - מוריה format
            sd_total = Paragraph(
                self._format_hebrew(f"סה\"כ לתת כתב: {sub_doc_code}  {sub_doc.get('name_he', '')}  {sub_doc_total:,.2f}"),
                ParagraphStyle(
                    'SubDocTotal',
                    fontName='HebrewFont-Bold',
                    fontSize=11,
                    textColor=colors.white,
                    backColor=self.PRIMARY_COLOR,
                    alignment=TA_RIGHT,
                    spaceAfter=15,
                    spaceBefore=5,
                    leftIndent=5,
                    rightIndent=5
                )
            )
            story.append(sd_total)
            story.append(PageBreak())

        # Terms and conditions
        story.extend(self._create_terms_and_conditions())

        # Build PDF
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


def generate_hierarchical_boq_pdf(
    boq_data: Dict[str, Any],
    logo_path: Optional[str] = None,
    company_name: Optional[str] = None
) -> io.BytesIO:
    """
    Generate professional hierarchical BOQ PDF with 4-level structure.

    Args:
        boq_data: Hierarchical BOQ data from build_hierarchy_response
        logo_path: Optional path to company logo
        company_name: Optional company name

    Returns:
        BytesIO buffer with PDF content
    """
    generator = ProfessionalBOQPDFGenerator()
    return generator.generate_hierarchical_pdf(boq_data, logo_path=logo_path, company_name=company_name)
