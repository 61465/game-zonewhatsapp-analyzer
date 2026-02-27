import streamlit as st
import pandas as pd
import re
import plotly.express as px
from collections import Counter
import time

# --- إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="Game Zone | WhatsApp Analyzer", layout="wide")

# تصميم CSS مخصص للثيم الأسود والذهبي
st.markdown("""
    <style>
    .main { background-color: #0a0a0a; color: #e0e0e0; }
    .stMetric { background-color: #1a1a1a; border-right: 5px solid #D4AF37; padding: 15px; border-radius: 5px; }
    div[data-testid="stMetricValue"] { color: #D4AF37; }
    .css-10trblm { color: #D4AF37; } /* العناوين */
    h1, h2, h3 { color: #D4AF37 !important; border-bottom: 1px solid #333; }
    .stButton>button { background-color: #D4AF37; color: black; border-radius: 20px; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- وظائف معالجة البيانات ---
class WhatsAppAnalyzer:
    def __init__(self, file_lines):
        self.lines = file_lines
        self.df = None

    def parse_data(self):
        """تحويل النص الخام إلى DataFrame منظم"""
        # نمط Regex ذكي يدعم معظم تنسيقات أندرويد وآيفون
        pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?::\d{2})?\s?[APM]*)\s-\s([^:]+):\s(.+)'
        
        extracted_data = []
        for line in self.lines:
            match = re.match(pattern, line)
            if match:
                extracted_data.append(match.groups())
        
        self.df = pd.DataFrame(extracted_data, columns=['Date', 'Time', 'User', 'Message'])
        return self.df

    def get_top_words(self, n=10):
        """تحليل الكلمات مع تصفية الكلمات الشائعة"""
        # قائمة الكلمات التي يجب تجاهلها (Stopwords)
        stop_words = set(['من', 'على', 'في', 'إلى', 'هذا', 'كان', 'أو', 'ما', 'لا', 'هل', 'يا', 'إلي', 'تم', 'عن', 'مع', 'هذه', 'اللي', 'ان', 'اللى'])
        
        all_text = " ".join(self.df['Message']).lower()
        # تنظيف النص من الرموز
        words = re.findall(r'\b\w{3,}\b', all_text) # الكلمات التي طولها أكثر من 2 حرف فقط
        filtered_words = [word for word in words if word not in stop_words]
        
        return Counter(filtered_words).most_common(n)

# --- واجهة المستخدم ---
st.title("🎮 GAME ZONE - WHATSAPP ANALYZER")
st.write("حلل محادثاتك بأسلوب المحترفين")

uploaded_file = st.file_uploader("قم برفع ملف الدردشة (txt)", type="txt")

if uploaded_file:
    # قراءة البيانات
    bytes_data = uploaded_file.getvalue().decode("utf-8").splitlines()
    analyzer = WhatsAppAnalyzer(bytes_data)
    
    # تأثير التحميل (الساعة الرملية)
    with st.status("جاري استخراج البيانات وتحليلها...", expanded=True) as status:
        st.write("🔍 فحص بنية الملف...")
        df = analyzer.parse_data()
        time.sleep(1)
        st.write("📊 حساب الإحصائيات الشخصية...")
        time.sleep(1)
        st.write("🧠 تحليل الكلمات الأكثر تكراراً...")
        status.update(label="اكتمل التحليل بنجاح!", state="complete", expanded=False)

    if not df.empty:
        # الصف الأول: إحصائيات سريعة
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي الرسائل", f"{len(df):,}")
        col2.metric("عدد المشاركين", df['User'].nunique())
        col3.metric("متوسط الكلمات/رسالة", round(df['Message'].str.split().str.len().mean(), 1))

        st.markdown("---")

        # الصف الثاني: الرسوم البيانية
        left_column, right_column = st.columns(2)

        with left_column:
            st.subheader("👥 توزيع الرسائل حسب الأشخاص")
            user_counts = df['User'].value_counts().reset_index()
            user_counts.columns = ['المستخدم', 'عدد الرسائل']
            fig_users = px.pie(user_counts, values='عدد الرسائل', names='المستخدم', 
                             color_discrete_sequence=px.colors.sequential.Goldenrod)
            fig_users.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_users, use_container_width=True)

        with right_column:
            st.subheader("🏆 الكلمات العشر الأكثر تكراراً")
            top_words = analyzer.get_top_words(10)
            words_df = pd.DataFrame(top_words, columns=['الكلمة', 'التكرار'])
            fig_words = px.bar(words_df, x='التكرار', y='الكلمة', orientation='h',
                             color_discrete_sequence=['#D4AF37'])
            fig_words.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_words, use_container_width=True)

        # عرض عينة من البيانات المنظمة
        with st.expander("📝 عرض البيانات المحللة بالكامل"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("❌ لم يتم العثور على بيانات صالحة. تأكد من تصدير الدردشة بشكل صحيح من واتساب.")

else:
    st.info("💡 نصيحة: اذهب إلى واتساب -> الإعدادات -> الدردشات -> سجل الدردشات -> نقل الدردشة (بدون وسائط) للحصول على الملف.")