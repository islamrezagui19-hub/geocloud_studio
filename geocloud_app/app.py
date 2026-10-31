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
uploaded_file = st.sidebar.file_uploader("قم برفع ملف .LAS للبئر:", type=["las"])

las_data = None

if uploaded_file is not None:
    try:
        content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        las_data = lasio.read(content)
        st.sidebar.success("تم قراءة الملف بنجاح!")
    except Exception as e:
        st.sidebar.error(f"حدث خطأ أثناء قراءة الملف: {e}")
else:
    st.sidebar.info("يرجى رفع ملف .LAS من القائمة الجانبية للبدء.")

# 3. معالجة وعرض البيانات
if las_data is not None:
    # تحويل الملف إلى DataFrame وتنظيف القيم الناقصة مثل -999.25
    df = las_data.df().reset_index()
    df.replace(-999.25, np.nan, inplace=True)
    df.replace(-9999, np.nan, inplace=True)
    
    available_columns = list(df.columns)
    
    st.sidebar.subheader("🎯 تحديد أسماء المنحنيات")
    
    # اختيار منحنى العمق
    default_depth = next((col for col in available_columns if 'DEP' in col.upper() or 'INDEX' in col.upper()), available_columns[0])
    depth_col = st.sidebar.selectbox("منحنى العمق (Depth):", available_columns, index=available_columns.index(default_depth))
    
    # اختيار باقي المنحنيات
    gr_col = st.sidebar.selectbox("منحنى أشعة غاما (Gamma Ray):", ["لا يوجد"] + available_columns, index=1 if len(available_columns)>1 else 0)
    res_col = st.sidebar.selectbox("منحنى المقاومية (Resistivity):", ["لا يوجد"] + available_columns, index=2 if len(available_columns)>2 else 0)
    por_col = st.sidebar.selectbox("منحنى المسامية (Porosity):", ["لا يوجد"] + available_columns, index=3 if len(available_columns)>3 else 0)

    tab1, tab2, tab3 = st.tabs(["📊 عارض التسجيلات", "🔬 المجهر الافتراضي", "📝 التصحيح الآلي"])
    
    # التبويب الأول: عارض منحنيات الآبار
    with tab1:
        st.subheader("تحليل تسجيلات الآبار (Well Logs)")
        
        # تصفية العمق
        min_depth = float(df[depth_col].min())
        max_depth = float(df[depth_col].max())
        selected_depth = st.slider("حدد مجال العمق (متر):", min_depth, max_depth, (min_depth, min_depth + 200.0))
        
        df_sub = df[(df[depth_col] >= selected_depth[0]) & (df[depth_col] <= selected_depth[1])]
        
        # إنشاء الرسم التفاعلي
        fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=(f'Gamma Ray ({gr_col})', f'Resistivity ({res_col})', f'Porosity ({por_col})'))
        
        if gr_col != "لا يوجد" and gr_col in df_sub.columns:
            fig.add_trace(go.Scatter(x=df_sub[gr_col], y=df_sub[depth_col], mode='lines', name='GR', line=dict(color='green')), row=1, col=1)
            
        if res_col != "لا يوجد" and res_col in df_sub.columns:
            fig.add_trace(go.Scatter(x=df_sub[res_col], y=df_sub[depth_col], mode='lines', name='Resistivity', line=dict(color='red')), row=1, col=2)
            fig.update_xaxes(type="log", row=1, col=2)
            
        if por_col != "لا يوجد" and por_col in df_sub.columns:
            fig.add_trace(go.Scatter(x=df_sub[por_col], y=df_sub[depth_col], mode='lines', name='Porosity', line=dict(color='blue')), row=1, col=3)
            
        fig.update_yaxes(autorange="reversed", title_text="العمق (متر)")
        fig.update_layout(height=650, title_text="تسجيلات البئر التفاعلية")
        
        st.plotly_chart(fig, use_container_width=True)
        
        if por_col != "لا يوجد" and por_col in df_sub.columns:
            avg_phi = df_sub[por_col].mean()
            # تعديل النسبة إذا كانت القيم بين 0 و 1 أو مئوية
            if avg_phi < 1.0:
                avg_phi *= 100          st.metric(label=f"متوسط المسامية ({por_col}) للنطاق المختار", value=f"{avg_phi:.2f} %")
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
        ans = st.number_input("أدخل قيمة المسامية المتوسطة التي حسبتها للنطاق المختار:", min_value=0.0, max_value=100.0)
        if st.button("تأكيد وتسليم الإجابة"):
            if por_col != "لا يوجد" and por_col in df_sub.columns:
                target = df_sub[por_col].mean()
                if target < 1.0:
                    target *= 100
                if abs(ans - target) < 1.5:
                    st.success(f"إجابة صحيحة وممتازة! القيمة المحسوبة: {target:.2f}%")
                else:
                    st.error(f"إجابة غير دقيقة. القيمة الصحيحة هي: {target:.2f}%")
