from graph import graph

""" Codigo simple para probar desde consola"""
def stream_graph_updates(user_input: str):
    """Stream the graph updates"""
    try:
        # Inicializa el estado con el mensaje del usuario
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        
        # Corre el grafo y devuelve el resultado
        result = graph.invoke(initial_state)
        
        # Imprime la respuesta del asistente desde el campo de respuesta
        if "response" in result:
            print("Assistant:", result["response"])
        else:
            print("Assistant: No response generated")
    except Exception as e:
        print(f"Error en el procesamiento: {e}")

def main():
    """Función principal para ejecutar el chat interactivo"""
    print("¡Bienvenido al clon digital de Nico!")
    print("Escribe 'quit', 'exit' o 'q' para salir.")
    
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("¡Hasta luego!")
                break
            stream_graph_updates(user_input)
        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
