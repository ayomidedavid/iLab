#1. 1. Printing a message Write a Python program that prints the message: Hello, World!
print("Hellow, World!")


#2. Greeting with name Ask the user to type their name. Print: Hello, <name>! Nice to meet you.
name = input("enter you name ")
print("Hello", name, "Nuce to meet you")


#3. Adding two numbers Ask the user to enter two numbers. Add them and print in a full sentence: The sum of 8 and 12 is 20.
num1 = int(input("enter any number"))
num2 = int(input("enter any number"))

sum = num1 + num2
print("the sume of ", num1, "and", num2, "is", sum)


#4. Converting Celsius to Fahrenheit Ask for a temperature in Celsius. Convert it to Fahrenheit using: F = (C × 9/5) + 32 and print the result.
temperature  = float(input("enter temperature in celcius"))
F = (temperature * 9/5) + 32
print("the result is ", F, "Fahrenheit")


#5. Even or odd Ask the user for an integer. Print whether it is even or odd.

integer = int(input("enter any integer"))
if integer % 2 != 0:
    print("the number is odd")
else:
    print("the number is even")



#6. Age input Ask the user for their age. Print: You are X years old.
age = int(input("Enter your age"))
print("you are ",age, "years old")


#7. . Birth year to age Ask for birth year. Subtract from current year to calculate and print age.
current_year = 2025
birth_year = int(input("enter the year you were born"))
age = current_year - birth_year
print("your age is ", age)


#8.  Rectangle area and perimeter Ask for length and width. Print both the area and perimeter.
length = float(input("enter the length of rectangle"))
width = float(input("enter the width of rectangle"))
area = length * width
perimeter = 2 * (length + width)
print("the area of rectangle is ", area)
print("the perimeter of rectangle is ", perimeter)



#9. Circle calculations Ask for radius. Print area and circumference.
radius = float(input("enter the radius of circle"))
pie = 3.14
area = pie * radius * radius
circumference = 2 * pie * radius    
print("the area of circle is ", area)
print("the circumference of circle is ", circumference)



#10. Square of a number Ask for a number. Print its square.
square =int(input("enter any number"))
square_of_number = square * square
print("the square of ", square, "is", square_of_number)



#11. Cube of a number Ask for a number. Print its cube.
cube = int(input("enter any number"))
cube_of_number = cube * cube * cube
print("the cube of ", cube, "is", cube_of_number)



#12.  Square root Ask for a number. Print its square root.
squareroort = int(input("enter any number"))
square_of_number = squareroort ** 0.5
print("the square root of ", squareroort, "is", square_of_number)



#13. Larger of two numbers Ask for two numbers. Print the larger one.
num1 = int(input("enter the first number"))
num2 = int(input("enter the second number"))

if num1 > num2:
    print(num1, "is greater than", num2)
else:
    print(num2, "is greater than", num1)



#14. Largest and smallest of three numbers Ask for three numbers. Print the largest and smallest
num1 = int(input("enter the first number"))
num2 = int(input("enter the second number"))
num3 = int(input("enter the third number"))

if num1>num2 and num1>num3:
    print(num1, "is the largest number")
    if num2<num3:
        print(num2, "is the smallest number")
    else:
        print(num3, "is the smallest number")
elif num2>num1 and num2>num3:
    print(num2, "is the largest number")
    if num1<num3:
        print(num1, "is the smallest number")
    else:
        print(num3, "is the smallest number")
else:
    print(num3, "is the largest number")
    if num1<num2:
        print(num1, "is the smallest number")
    else:
        print(num2, "is the smallest number")




#15. 






check = int(input("enter any number"))
if check >= 1 and check <=100:
    print("the number is in between 1 to 100")
else:
    print("the number is not in between 1 to 100")