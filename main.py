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

# --- 1. كلاس المحلل ---
class WhatsAppAnalyzer:
    def __init__(self, content):
        self.content = content
        self.df = self._process_data()

    def _process_data(self):
        # نمط يدعم أغلب صيغ أجهزة الأندرويد والآيفون
        pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?[ap]m?)\s-\s([^:]+):\s(.*)$'
        data = []
        for line in self.content:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                date_time, user, message = match.groups()
                data.append({
                    'DateTime': date_time,
                    'User': user.strip(),
                    'Message': message.strip()
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        return df

    def get_top_words(self, n=15):
        if self.df.empty: return []
        all_text = " ".join(self.df['Message'].astype(str)).lower()
        words = re.findall(r'\w+', all_text)
        stop_words = {'media', 'omitted', 'الرسالة', 'تم', 'حذف', 'هذا', 'من', 'على', 'في', 'إلى', 'لا', 'ما'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        return Counter(filtered_words).most_common(n)

# --- 2. دالة توليد تقرير PDF ---
def generate_pdf_report(df, analyzer):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # رأس الصفحة
    c.setFillColorRGB(0.8, 0.6, 0.2)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "WhatsApp Analysis Report")
    
    # إحصائيات
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, f"Total Messages: {len(df)}")
    c.drawString(50, height - 120, f"Participants: {df['User'].nunique()}")
    c.drawString(50, height - 140, f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    
    # الرسم البياني
    if not df.empty:
        user_counts = df['User'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(5, 3))
        user_counts.plot(kind='barh', ax=ax, color='#D4AF37')
        plt.tight_layout()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
            fig.savefig(tmpfile.name, format='png', dpi=100)
            img_path = tmpfile.name
        
        c.drawImage(ImageReader(img_path), 50, height - 400, width=300, height=180)
        plt.close(fig)
        os.unlink(img_path)

    # الكلمات الأكثر تكراراً
    top_words = analyzer.get_top_words(10)
    if top_words:
        c.drawString(400, height - 150, "Top Keywords:")
        y = height - 170
        for i, (word, count) in enumerate(top_words, 1):
            c.setFont("Helvetica", 10)
            c.drawString(400, y, f"{i}. {word}: {count}")
            y -= 15

    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# --- 3. واجهة Streamlit ---
st.set_page_config(page_title="Game Zone Analyzer", layout="wide")
st.title("WhatsApp Chat Analyzer 📊")

file = st.file_uploader("Upload Chat File (.txt)", type="txt")

if file:
    content = file.getvalue().decode("utf-8").splitlines()
    analyzer = WhatsAppAnalyzer(content)
    df = analyzer.df

    if not df.empty:
        st.success(f"Successfully loaded {len(df)} messages!")
        
        # أزرار التحميل والمعالجة
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Generate & Download PDF Report", use_container_width=True):
                with st.spinner("Creating PDF..."):
                    pdf_data = generate_pdf_report(df, analyzer)
                    st.download_button(
                        label="Click to Save PDF",
                        data=pdf_data,
                        file_name="whatsapp_analysis.pdf",
                        mime="application/pdf"
                    )
        
        # عرض البيانات للمستخدم
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.error("Could not parse the file. Please check the chat format.")
