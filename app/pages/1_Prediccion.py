# ESTADO_ARCHIVO: EN_MODIFICACION
import streamlit as st
from pydantic import ValidationError

from app.client import ErrorAPI
from api.schemas import Cliente
from app.ui import asegurar_navegacion, cabecera, mostrar_resultados, api_activa

asegurar_navegacion("pages/1_Prediccion.py")

cabecera("prediccion", "01 / PERFIL DEL CLIENTE", "Una persona, dos perspectivas.",
         "Completa el perfil para comparar la probabilidad de abandono y el nivel de riesgo de ambos modelos.")
predictor = api_activa()
with st.form("cliente"):
    st.subheader("Cuenta y permanencia")
    left, right = st.columns(2)
    months = left.number_input("Antigüedad (meses)", 0, 1200, 12)
    charges = right.number_input("Cargos mensuales", 0.0, value=50.0, step=1.0)
    contract = left.selectbox("Contrato", ["Mes a mes", "Un año", "Dos años"])
    payment = right.selectbox("Método de pago", ["Cheque electrónico", "Cheque por correo", "Transferencia automática", "Tarjeta automática"])
    electronic = st.checkbox("Facturación electrónica")
    st.subheader("Perfil y servicios")
    left, right = st.columns(2)
    with left:
        senior = st.checkbox("Adulto mayor")
        partner = st.checkbox("Tiene pareja")
        dependents = st.checkbox("Tiene dependientes")
        phone = st.checkbox("Servicio telefónico", value=True)
        lines = st.checkbox("Líneas múltiples")
    with right:
        internet = st.selectbox("Servicio de internet", ["DSL", "Fibra óptica", "Sin internet"])
        extras = st.multiselect("Servicios de internet contratados", ["Seguridad online", "Copia de seguridad", "Protección de dispositivos", "Soporte técnico", "Streaming TV", "Streaming películas"])
    submitted = st.form_submit_button("Comparar predicciones", type="primary")
if submitted:
    data = {"Adulto_Mayor": int(senior), "Pareja": int(partner), "Dependientes": int(dependents),
            "Antiguedad(Meses)": months, "Servicio_Telefono": int(phone), "Lineas_Multiples": int(lines),
            "Internet_DSL": int(internet == "DSL"), "Internet_Fiber optic": int(internet == "Fibra óptica"),
            "Seguridad_Online": int("Seguridad online" in extras), "Copia_Seguridad_Online": int("Copia de seguridad" in extras),
            "Proteccion_Dispositivos": int("Protección de dispositivos" in extras), "Soporte_Tecnico": int("Soporte técnico" in extras),
            "Streaming_TV": int("Streaming TV" in extras), "Streaming_Peliculas": int("Streaming películas" in extras),
            "Contrato": ["Mes a mes", "Un año", "Dos años"].index(contract), "Facturacion_Electronica": int(electronic),
            "MP_Electronic check": int(payment == "Cheque electrónico"), "MP_Mailed check": int(payment == "Cheque por correo"),
            "MP_Bank transfer (automatic)": int(payment == "Transferencia automática"), "Cargos_Mensuales": charges}
    try:
        result = predictor.predecir([Cliente.model_validate(data)], individual=True)
        mostrar_resultados(result, predictor.config)
    except (ValidationError, ErrorAPI) as exc:
        st.error(str(exc))
