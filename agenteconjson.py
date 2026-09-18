from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import StateGraph

import json

ARCHIVO_TARJETAS = "tarjetas.json"

def cargar_tarjetas():
    try:
        with open(ARCHIVO_TARJETAS, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_tarjetas(datos):
    with open(ARCHIVO_TARJETAS, "w") as f:
        json.dump(datos, f, indent=2)

tarjetas = cargar_tarjetas()

@tool
def add_card(nombre: str, color: str) -> str:
    """Add a card (verde, amarilla, or roja) to a person's count."""
    if nombre not in tarjetas:
        tarjetas[nombre] = {"verde": 0, "amarilla": 0, "roja": 0}

    tarjetas[nombre][color] += 1
    guardar_tarjetas(tarjetas)

    return f"{nombre} ahora tiene {tarjetas[nombre][color]} tarjeta(s) {color}(s)."


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
    convo = [HumanMessage(content="Suma una tarjeta roja a Diego.")]
    result = graph.invoke({"messages": convo})

    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")

 
