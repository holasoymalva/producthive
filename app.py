import streamlit as st
from datetime import datetime, timedelta
import json
import anthropic
import pandas as pd
import plotly.express as px
from typing import List, Dict
import os
import pytz

# Configuración inicial de Streamlit
st.set_page_config(
    page_title="Asistente Virtual de Productividad",
    page_icon="✨",
    layout="wide"
)

# Inicialización de variables de sesión
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = {}
if 'habits' not in st.session_state:
    st.session_state.habits = []

# Configuración de la API de Anthropic
class ProductivityAssistant:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        self.current_timezone = pytz.timezone('America/Mexico_City')

    def get_assistant_response(self, prompt: str) -> str:
        """Obtiene una respuesta del asistente de Anthropic"""
        try:
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content
        except Exception as e:
            st.error(f"Error al comunicarse con el asistente: {str(e)}")
            return "Lo siento, ha ocurrido un error al procesar tu solicitud."

    def create_schedule(self, tasks: List[Dict]) -> Dict:
        """Crea un horario optimizado basado en las tareas proporcionadas"""
        prompt = f"""Por favor, crea un horario optimizado para las siguientes tareas:
        {json.dumps(tasks, indent=2)}
        Ten en cuenta la prioridad y duración de cada tarea.
        Devuelve el horario en formato JSON con horas específicas."""
        
        response = self.get_assistant_response(prompt)
        try:
            return json.loads(response)
        except:
            return {}

    def analyze_habits(self, habits_data: List[Dict]) -> str:
        """Analiza los hábitos del usuario y proporciona recomendaciones"""
        prompt = f"""Analiza los siguientes datos de hábitos y productividad:
        {json.dumps(habits_data, indent=2)}
        Proporciona recomendaciones específicas para mejorar la productividad."""
        
        return self.get_assistant_response(prompt)

# Interfaz de usuario
def main():
    st.title("✨ Asistente Virtual de Productividad")
    
    # Inicializar el asistente
    assistant = ProductivityAssistant()
    
    # Sidebar para navegación
    page = st.sidebar.selectbox(
        "Selecciona una función",
        ["Tareas", "Horario", "Análisis de Hábitos", "Configuración"]
    )
    
    if page == "Tareas":
        show_tasks_page(assistant)
    elif page == "Horario":
        show_schedule_page(assistant)
    elif page == "Análisis de Hábitos":
        show_habits_page(assistant)
    elif page == "Configuración":
        show_settings_page()

def show_tasks_page(assistant: ProductivityAssistant):
    st.header("📝 Gestión de Tareas")
    
    # Formulario para agregar tareas
    with st.form("nueva_tarea"):
        col1, col2, col3 = st.columns(3)
        with col1:
            titulo = st.text_input("Título de la tarea")
        with col2:
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
        with col3:
            fecha_limite = st.date_input("Fecha límite")
            
        descripcion = st.text_area("Descripción")
        submitted = st.form_submit_button("Agregar Tarea")
        
        if submitted and titulo:
            nueva_tarea = {
                "titulo": titulo,
                "prioridad": prioridad,
                "fecha_limite": fecha_limite.strftime("%Y-%m-%d"),
                "descripcion": descripcion,
                "completada": False
            }
            st.session_state.tasks.append(nueva_tarea)
            st.success("Tarea agregada exitosamente")

    # Mostrar tareas existentes
    st.subheader("Tareas Pendientes")
    for i, tarea in enumerate(st.session_state.tasks):
        if not tarea["completada"]:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{tarea['titulo']}**")
                st.write(tarea['descripcion'])
            with col2:
                st.write(f"Prioridad: {tarea['prioridad']}")
                st.write(f"Fecha límite: {tarea['fecha_limite']}")
            with col3:
                if st.button("Completar", key=f"complete_{i}"):
                    tarea["completada"] = True
                    st.rerun()

def show_schedule_page(assistant: ProductivityAssistant):
    st.header("📅 Horario Personalizado")
    
    # Crear nuevo horario
    if st.button("Generar Horario Optimizado"):
        tareas_pendientes = [t for t in st.session_state.tasks if not t["completada"]]
        if tareas_pendientes:
            horario = assistant.create_schedule(tareas_pendientes)
            st.session_state.schedule = horario
            st.success("Horario generado exitosamente")
        else:
            st.warning("No hay tareas pendientes para generar un horario")
    
    # Mostrar horario actual
    if st.session_state.schedule:
        st.subheader("Tu Horario")
        df_horario = pd.DataFrame(st.session_state.schedule.items(), columns=['Hora', 'Actividad'])
        st.dataframe(df_horario)
        
        # Visualización del horario
        fig = px.timeline(
            df_horario,
            x_start='Hora',
            y='Actividad',
            title="Distribución del Tiempo"
        )
        st.plotly_chart(fig)

def show_habits_page(assistant: ProductivityAssistant):
    st.header("📊 Análisis de Hábitos")
    
    # Registro de hábitos
    with st.form("registro_habitos"):
        fecha = st.date_input("Fecha")
        horas_trabajo = st.number_input("Horas de trabajo", 0, 24)
        descansos = st.number_input("Número de descansos", 0, 10)
        nivel_energia = st.slider("Nivel de energía", 1, 10)
        
        if st.form_submit_button("Registrar"):
            nuevo_registro = {
                "fecha": fecha.strftime("%Y-%m-%d"),
                "horas_trabajo": horas_trabajo,
                "descansos": descansos,
                "nivel_energia": nivel_energia
            }
            st.session_state.habits.append(nuevo_registro)
            st.success("Hábito registrado exitosamente")
    
    # Análisis de hábitos
    if st.session_state.habits:
        st.subheader("Tendencias")
        df_habits = pd.DataFrame(st.session_state.habits)
        
        # Gráficas de tendencias
        col1, col2 = st.columns(2)
        with col1:
            fig_trabajo = px.line(df_habits, x='fecha', y='horas_trabajo', title='Horas de Trabajo por Día')
            st.plotly_chart(fig_trabajo)
        with col2:
            fig_energia = px.line(df_habits, x='fecha', y='nivel_energia', title='Nivel de Energía por Día')
            st.plotly_chart(fig_energia)
        
        # Recomendaciones del asistente
        if st.button("Obtener Recomendaciones"):
            recomendaciones = assistant.analyze_habits(st.session_state.habits)
            st.info(recomendaciones)

def show_settings_page():
    st.header("⚙️ Configuración")
    
    # Configuración de zona horaria
    timezone = st.selectbox(
        "Zona Horaria",
        pytz.all_timezones,
        index=pytz.all_timezones.index('America/Mexico_City')
    )
    
    # Configuración de notificaciones
    st.subheader("Notificaciones")
    email_notifications = st.checkbox("Recibir notificaciones por email")
    if email_notifications:
        email = st.text_input("Email para notificaciones")
    
    # Exportar datos
    if st.button("Exportar Datos"):
        data = {
            "tasks": st.session_state.tasks,
            "schedule": st.session_state.schedule,
            "habits": st.session_state.habits
        }
        st.download_button(
            label="Descargar datos",
            data=json.dumps(data, indent=2),
            file_name="productivity_data.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()