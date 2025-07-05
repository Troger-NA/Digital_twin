from graph import graph

def stream_graph_updates(user_input: str):
    """Stream the graph updates"""
    try:
        # Initialize the state with the user message
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        # Run the graph and get the final result
        result = graph.invoke(initial_state)
        # Print the assistant's response from the response field
        if "response" in result:
            print("\n========== [BOT RESPONSE] ==========")
            print(result["response"])
            print("====================================\n")
        else:
            print("Assistant: No response generated")
    except Exception as e:
        print(f"Error en el procesamiento: {e}")

def main():
    """Main function to run the interactive chat"""
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