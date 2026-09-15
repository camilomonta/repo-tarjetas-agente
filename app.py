from flask import Flask, request, render_template_string
from agente import graph, obtener_todas_las_tarjetas
from langchain_core.messages import HumanMessage

app = Flask(__name__)

FORM_HTML = """
<!doctype html>
<title>Tarjetas de comportamiento</title>
<h1>Registrar tarjeta</h1>
<form method="post">
  <input type="text" name="mensaje" size="60" placeholder="Ej: dale una tarjeta amarilla a Lina">
  <button type="submit">Enviar</button>
</form>
{% if respuesta %}
<h2>Respuesta:</h2>
<pre>{{ respuesta }}</pre>
{% endif %}

<h2>Conteo actual</h2>
<table border="1" cellpadding="5">
  <tr><th>Nombre</th><th>Verde</th><th>Amarilla</th><th>Roja</th></tr>
  {% for nombre, conteo in tarjetas.items() %}
  <tr>
    <td>{{ nombre }}</td>
    <td>{{ conteo['verde'] }}</td>
    <td>{{ conteo['amarilla'] }}</td>
    <td>{{ conteo['roja'] }}</td>
  </tr>
  {% endfor %}
</table>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    respuesta = None
    if request.method == "POST":
        mensaje = request.form["mensaje"]
        convo = [HumanMessage(content=mensaje)]
        result = graph.invoke({"messages": convo})
        lines = [f"{m.type}: {m.content}" for m in result["messages"]]
        respuesta = "\n".join(lines)

    tarjetas_actuales = obtener_todas_las_tarjetas()
    return render_template_string(FORM_HTML, respuesta=respuesta, tarjetas=tarjetas_actuales)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
EOF