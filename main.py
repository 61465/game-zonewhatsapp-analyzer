# أضف هذا الاستيراد في بداية الملف
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import matplotlib.pyplot as plt
import tempfile
import os

# أضف هذه الدالة داخل class WhatsAppAnalyzer أو كدالة منفصلة
def generate_pdf_report(df, analyzer):
    """توليد تقرير PDF بالإحصائيات"""
    
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # عنوان التقرير
    c.setFillColorRGB(0.8, 0.6, 0.2)  # ذهبي
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Game Zone - WhatsApp Analysis Report")
    
    # إحصائيات سريعة
    c.setFillColorRGB(0, 0, 0)  # أسود
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, f"إجمالي الرسائل: {len(df)}")
    c.drawString(50, height - 120, f"عدد المشاركين: {df['User'].nunique()}")
    c.drawString(50, height - 140, f"تاريخ التحليل: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    
    # حفظ الرسم البياني للأعضاء كصورة مؤقتة
    user_counts = df['User'].value_counts().head(10)  # أهم 10 أشخاص فقط للـ PDF
    fig, ax = plt.subplots(figsize=(6, 4))
    user_counts.plot(kind='barh', ax=ax, color='#D4AF37')
    ax.set_title("توزيع الرسائل حسب الأشخاص", fontsize=12, fontweight='bold')
    ax.set_xlabel("عدد الرسائل")
    plt.tight_layout()
    
    # حفظ الصورة في ملف مؤقت
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
        fig.savefig(tmpfile.name, format='png', bbox_inches='tight', dpi=100)
        tmpfile_path = tmpfile.name
    
    plt.close(fig)
    
    # إدراج الصورة في PDF
    img = ImageReader(tmpfile_path)
    c.drawImage(img, 50, height - 400, width=300, height=200)
    
    # تنظيف الملف المؤقت
    os.unlink(tmpfile_path)
    
    # إضافة الكلمات الأكثر تكراراً
    c.setFillColorRGB(0.8, 0.6, 0.2)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(400, height - 150, "🏆 الكلمات الأكثر تكراراً")
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    top_words = analyzer.get_top_words(15)
    y_position = height - 180
    for i, (word, count) in enumerate(top_words, 1):
        c.drawString(400, y_position, f"{i}. {word}: {count} مرة")
        y_position -= 20
        if y_position < 100:  # صفحة جديدة إذا لزم الأمر
            c.showPage()
            y_position = height - 50
    
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# ثم أضف هذا الزر في نهاية الكود (قبل عرض البيانات)
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📥 تحميل التقرير كـ PDF", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير..."):
            pdf_file = generate_pdf_report(df, analyzer)
            st.download_button(
                label="اضغط لتحميل التقرير",
                data=pdf_file,
                file_name=f"whatsapp_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
