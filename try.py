def simple_generator():
    yield 1
    yield 2
    yield 3

# Create a generator object
gen = simple_generator()

# Iterate through the generator
for num in gen:
    print(num)