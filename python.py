def add(x, y):
    return x + y
     print("addition successsful ")
def subtract(x, y):
    return x - y
     print("substraction successsful ")
def multiply(x, y):
    print("multiplication successsful ")
    print("multiplication2 successsful ")
    return x * y

def divide(x, y):
    if y == 0:
        return "Error: Cannot divide by zero"
    return x / y
print("divide  successsful for the above operator ")

def calculator():
    print("Simple Calculator")
    print("------------------")
    print("Select operation:")
    print("1. Add (+)")
    print("2. Subtract (-)")
    print("3. Multiply (*)")
    print("4. Divide (/)")
    
    choice = input("Enter choice (1/2/3/4): ")

    if choice not in ['1', '2', '3', '4']:
        print("Invalid input")
        return

    try:
        num1 = float(input("Enter first number: "))
        num2 = float(input("Enter second number: "))
    except ValueError:
        print("Invalid number entered.")
        return

    if choice == '1':
        result = add(num1, num2)
        op = '+'
    elif choice == '2':
        result = subtract(num1, num2)
        op = '-'
    elif choice == '3':
        result = multiply(num1, num2)
        op = '*'
    elif choice == '4':
        result = divide(num1, num2)
        op = '/'

    print(f"{num1} {op} {num2} = {result}")

if __name__ == "__main__":
    calculator()
