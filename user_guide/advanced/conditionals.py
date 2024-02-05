import random

from flytekit import conditional, task, workflow


@task
def calculate_circle_circumference(radius: float) -> float:
    return 2 * 3.14 * radius  # Task to calculate the circumference of a circle


@task
def calculate_circle_area(radius: float) -> float:
    return 3.14 * radius * radius  # Task to calculate the area of a circle


@workflow
def shape_properties(radius: float) -> float:
    return (
        conditional("shape_properties")
        .if_((radius >= 0.1) & (radius < 1.0))
        .then(calculate_circle_circumference(radius=radius))
        .else_()
        .then(calculate_circle_area(radius=radius))
    )


if __name__ == "__main__":
    radius_small = 0.5
    print(f"Circumference of circle (radius={radius_small}): {shape_properties(radius=radius_small)}")

    radius_large = 3.0
    print(f"Area of circle (radius={radius_large}): {shape_properties(radius=radius_large)}")



@workflow
def shape_properties_with_multiple_branches(radius: float) -> float:
    return (
        conditional("shape_properties_with_multiple_branches")
        .if_((radius >= 0.1) & (radius < 1.0))
        .then(calculate_circle_circumference(radius=radius))
        .elif_((radius >= 1.0) & (radius <= 10.0))
        .then(calculate_circle_area(radius=radius))
        .else_()
        .fail("The input must be within the range of 0 to 10.")
    )