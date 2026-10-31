import streamlit as st
import lasio
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="GeoCloud Studio - Petrophysics MVP",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ GeoCloud Studio")
st.markdown("منصة سحابية تفاعلية لتفسير تسجيلات الآبار وفحص الشرائح الصخرية المجهرية.")

# 2. القائمة الجانبية لإدارة البيانات
st.sidebar.header("📁 إدارة البيانات")
data_option = st.sidebar.selectbox(
    "اختر مصدر البيانات:",
    ["رفع ملف .LAS محلي", "عرض التوضيح المباشر"]
)

las_data = None

if data_option == "رفع ملف .LAS محلي":
    uploaded_file = st.sidebar.file_uploader("قم برفع ملف LAS:", type=["las"])
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            las_data = lasio.read(content)
            st.sidebar.success("تم قراءة الملف بنجاح!")
        except Exception as e:
            st.sidebar.error(f"حدث خطأ أثناء قراءة الملف: {e}")
else:
    st.sidebar.info("يرجى رفع ملف .LAS من القائمة الجانبية لبدء التحليل.")

# 3. عرض البيانات والواجهة الرئيسية
if las_data is not None:
    df = las_data.df().reset_index()
    
    tab1, tab2, tab3 = st.tabs(["📊 عارض التسجيلات", "🔬 المجهر الافتراضي", "📝 التصحيح الآلي"])
    
    # التبويب الأول: عارض منحنيات الآبار
    with tab1:
        st.subheader("تحليل تسجيلات الآبار (Well Logs)")
        
        if 'DEPTH' in df.columns:
            min_depth = float(df['DEPTH'].min())
            max_depth = float(df['DEPTH'].max())
            selected_depth = st.slider("حدد مجال العمق (متر):", min_depth, max_depth, (min_depth, min_depth + 150.0))
            
            df_sub = df[(df['DEPTH'] >= selected_depth[0]) & (df['DEPTH'] <= selected_depth[1])]
            
            fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=('Gamma Ray (GR)', 'Resistivity (RD)', 'Porosity (NPHI)'))
            
            if 'GR' in df_sub.columns:
                fig.add_trace(go.Scatter(x=df_sub['GR'], y=df_sub['DEPTH'], mode='lines', name='GR', line=dict(color='green')), row=1, col=1)
                
            if 'RDEP' in df_sub.columns:
                fig.add_trace(go.Scatter(x=df_sub['RDEP'], y=df_sub['DEPTH'], mode='lines', name='Resistivity', line=dict(color='red')), row=1, col=2)
                fig.update_xaxes(type="log", row=1, col=2)
                
            if 'NPHI' in df_sub.columns:
                fig.add_trace(go.Scatter(x=df_sub['NPHI'], y=df_sub['DEPTH'], mode='lines', name='NPHI', line=dict(color='blue')), row=1, col=3)
                
            fig.update_yaxes(autorange="reversed", title_text="العمق (متر)")
            fig.update_layout(height=650, title_text="تسجيلات البئر التفاعلية")
            
            st.plotly_chart(fig, use_container_width=True)
            
            if 'NPHI' in df_sub.columns:
                avg_phi = df_sub['NPHI'].mean() * 100
                st.metric(label="متوسط المسامية للنطاق المختار", value=f"{avg_phi:.2f} %")

    # التبويب الثاني: المجهر الافتراضي
    with tab2:
        st.subheader("المجهر الافتراضي لشرائح صخور الخزان")
        col1, col2 = st.columns(2)
        with col1:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Thin_section_of_sandstone.jpg/640px-Thin_section_of_sandstone.jpg", caption="ضوء مستقطب أحادي (PPL)", use_column_width=True)
        with col2:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Thin_section_of_sandstone.jpg/640px-Thin_section_of_sandstone.jpg", caption="ضوء مستقطب متقاطع (XPL)", use_column_width=True)

    # التبويب الثالث: نظام التقييم الآلي
    with tab3:
        st.subheader("نظام الإجابة والتصحيح التلقائي") 
            

