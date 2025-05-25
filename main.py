from logic_chatbot import handle_message

def main():
    # 1) Welcome message
    print("Logic Chatbot")
    print("Type 'exit' to quit")

    # 2) Interactive loop
    while True:
        # a) prompt
        user_input = input("> ")

        # b) dispatch
        response = handle_message(user_input)

        # c) exit if handle_message returns None
        if response is None:
            print("Goodbye!")
            break

        # d) otherwise, show the chatbot’s reply
        print(response)

if __name__ == "__main__":
    main()
