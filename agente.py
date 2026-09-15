from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import StateGraph

def get_conexion():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        dbname=os.environ.get("DB_NAME", "tarjetas_db"),
        user=os.environ.get("DB_USER", "agente"),
        password=os.environ.get("DB_PASSWORD", "agente_pass"),
    )

@tool
def add_card(nombre: str, color: str) -> str:
    """Add a card (verde, amarilla, or roja) to a person's count."""
    conn = get_conexion()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO usuarios (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING",
        (nombre,)
    )

    cur.execute(
        """
        INSERT INTO tarjetas (usuario_id, color, cantidad)
        VALUES ((SELECT id FROM usuarios WHERE nombre = %s), %s, 1)
        ON CONFLICT (usuario_id, color)
        DO UPDATE SET cantidad = tarjetas.cantidad + 1
        """,
        (nombre, color)
    )

    cur.execute(
        """
        SELECT cantidad FROM tarjetas
        WHERE usuario_id = (SELECT id FROM usuarios WHERE nombre = %s) AND color = %s
        """,
        (nombre, color)
    )
    cantidad_actual = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return f"{nombre} ahora tiene {cantidad_actual} tarjeta(s) {color}(s)."

def obtener_todas_las_tarjetas():
    conn = get_conexion()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT usuarios.nombre, tarjetas.color, tarjetas.cantidad
        FROM tarjetas
        JOIN usuarios ON tarjetas.usuario_id = usuarios.id
        """
    )
    filas = cur.fetchall()
    cur.close()
    conn.close()

    resultado = {}
    for nombre, color, cantidad in filas:
        if nombre not in resultado:
            resultado[nombre] = {"verde": 0, "amarilla": 0, "roja": 0}
        resultado[nombre][color] = cantidad

    return resultado

def call_model(state):
    msgs = state["messages"]

    prompt = (
        '''You are an assistant that tracks colored cards (verde, amarilla, roja) given to people.
        When the user mentions giving a card to someone, call add_card with the person's name
        and the color (use lowercase: "verde", "amarilla", or "roja").
        Otherwise, just respond normally.'''
    )

    full = [SystemMessage(prompt)] + msgs

    first = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0).bind_tools([add_card]).invoke(full)
    out = [first]

    if getattr(first, "tool_calls", None):
        tc = first.tool_calls[0]
        result = add_card.invoke(tc["args"])
        out.append(ToolMessage(content=result, tool_call_id=tc["id"]))

        second = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0).invoke(full + out)
        out.append(second)

    return {"messages": out}

def construct_graph():
    g = StateGraph(dict)
    g.add_node("assistant", call_model)
    g.set_entry_point("assistant")
    return g.compile()

graph = construct_graph()

if __name__ == "__main__":
    convo = [HumanMessage(content="Le quiero dar una tarjeta amarilla a Lina.")]
    result = graph.invoke({"messages": convo})

    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")

    print("\n=== Estado actual de tarjetas ===")
    print(obtener_todas_las_tarjetas())
