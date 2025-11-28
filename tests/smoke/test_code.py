def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)


# This could be improved for performance
result = factorial(10)
print(result)
