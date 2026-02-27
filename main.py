import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import tempfile
import os
import re
from collections import Counter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- 1. كلاس المحلل الشامل لكل أنواع المحادثات ---
class WhatsAppAnalyzer:
    def __init__(self, content):
        self.content = content
        self.df = self._process_data()

    def _process_data(self):
        data = []
        # نمط عالمي: يبحث عن تاريخ في بداية السطر ثم اسم ثم رسالة
        # يدعم صيغ مثل: [27/02/2026] أو 27/02/26 أو 2026-02-27
        # ويدعم الفواصل المختلفة: " - " أو ": " أو " ] "
        pattern = r'^\[?(\d{1,4}[/\.-]\d{1,4}[/\.-]\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?\s?[apAP]?[mM]?)\]?[\s-]*([^:]+):\s(.*)$'
        
        for line in self.content:
            line = line.strip()
            if not line: continue
            
            match = re.match(pattern, line)
            if match:
                date_time, user, message = match.groups()
                data.append({
                    'DateTime': date_time,
                    'User': user.strip(),
                    'Message': message.strip()
                })
            else:
                # إذا كان السطر تكملة لرسالة سابقة (أسطر متعددة)
                if data:
                    data[-1]['Message'] += " " + line
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # محاولة ذكية لتحويل التاريخ مهما كانت الصيغة
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce', fuzzy=True)
            # حذف الرسائل التقنية التي لا تحتوي على محتوى فعلي
            tech_phrases = ['<Media omitted>', 'نتائج الوسائط محذوفة', 'الرسالة محذوفة', 'This message was deleted']
            df = df[~df['Message'].str.contains('|'.join(tech_phrases), na=False)]
            
        return df

    def get_top_words(self, n=15):
        if self.df.empty: return []
        text = " ".join(self.df['Message'].astype(str)).lower()
        words = re.findall(r'\w+', text)
        # قائمة كلمات شائعة لتنظيف النتائج
        stop_words = {'الرسالة', 'تم', 'حذف', 'هذا', 'من', 'على', 'في', 'إلى', 'omitted', 'media', 'the', 'and', 'was'}
        filtered = [w for w in words if w not in stop_words and len(w) > 2]
        return Counter(filtered).most_common(n)

# --- 2. دالة توليد تقرير PDF ---
def generate_pdf_report(df, analyzer):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # تنسيق رأس الصفحة
    c.setFillColorRGB(0.1, 0.2, 0.4)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 60, "WhatsApp Chat Analysis Report")
    
    c.setStrokeColorRGB(0.8, 0.6, 0.2)
    c.line(50, height - 70, width - 50, height - 70)
    
    # الإحصائيات العامة
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 110, "General Statistics:")
    c.setFont("Helvetica", 12)
    c.drawString(70, height - 135, f"• Total Messages Analyzed: {len(df)}")
    c.drawString(70, height - 155, f"• Active Participants: {df['User'].nunique()}")
    c.drawString(70, height - 175, f"• Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    
    # إضافة الرسم البياني
    if not df.empty:
        user_counts = df['User'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(5, 3))
        user_counts.sort_values().plot(kind='barh', ax=ax, color='#D4AF37')
        ax.set_title("Top 10 Active Users")
        plt.tight_layout()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
            fig.savefig(tmpfile.name, format='png', dpi=100)
            img_path = tmpfile.name
        
        c.drawImage(ImageReader(img_path), 50, height - 420, width=350, height=220)
        plt.close(fig)
        if os.path.exists(img_path): os.unlink(img_path)

    # الكلمات المفتاحية
    top_words = analyzer.get_top_words(10)
    if top_words:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 460, "Most Used Keywords:")
        y = height - 485
        c.setFont("Helvetica", 11)
        for i, (word, count) in enumerate(top_words, 1):
            c.drawString(70, y, f"{i}. {word} ({count} times)")
            y -= 18

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# --- 3. واجهة التطبيق (Streamlit UI) ---
st.set_page_config(page_title="WhatsApp Expert Analyzer", page_icon="📊", layout="wide")

st.title("📊 WhatsApp Chat Expert Analyzer")
st.info("قم برفع ملف الدردشة بصيغة .txt (بدءاً من التاريخ والاسم)")

uploaded_file = st.file_uploader("Upload your chat file", type="txt")

if uploaded_file:
    # قراءة المحتوى
    raw_content = uploaded_file.getvalue().decode("utf-8").splitlines()
    analyzer = WhatsAppAnalyzer(raw_content)
    df = analyzer.df

    if not df.empty:
        st.success(f"✅ Analysis Complete! Found {len(df)} messages.")
        
        # قسم التحميل
        st.markdown("### 📥 Download Report")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pdf_data = generate_pdf_report(df, analyzer)
            st.download_button(
                label="Click here to download PDF Report",
                data=pdf_data,
                file_name=f"Chat_Analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # عرض سريع للبيانات
        st.markdown("### 🔍 Data Preview")
        st.dataframe(df.head(20), use_container_width=True)
        
        # توزيع الرسائل حسب المستخدمين (بشكل حي في الموقع)
        st.markdown("### 📈 Message Distribution")
        st.bar_chart(df['User'].value_counts().head(15))
        
    else:
        st.error("❌ عذراً، لم نتمكن من التعرف على شكل الرسائل في هذا الملف. تأكد من تصدير الدردشة بشكل صحيح من واتساب.")
