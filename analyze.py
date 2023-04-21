#! /usr/bin/env python
import argparse
import csv
import re

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skewnorm

PERCENTILES = [10, 50, 90]
PERCENTILE_COLORS = ["red", "black", "green"]
# If True, we will make some assumptions about the data that favor a slightly
# longer life expectancy.
OPTIMISTIC_MODE = True


def get_data(data_path: str, min_age: int = 0) -> dict[int, int]:
    # Open CSV file
    death_count_by_age: dict[int, int] = {}
    with open(data_path) as f:
        # Parse the CSV into rows with headers
        reader = csv.DictReader(f)
        for row in reader:
            lower_age_str = re.match(r"(\d+)", row["age"]).group(1)  # "26-27" => 26
            age = int(lower_age_str)
            if age < min_age:
                # Don't include ages below the minimum
                continue
            death_count_without_commas = row["dx"].replace(",", "")
            death_count = int(death_count_without_commas)  # number of deaths column
            death_count_by_age[age] = death_count

    # If we're in optimistic mode and the deaths in the final bucket are greater
    # than the deaths in the second-to-last bucket, then we'll assume that the
    # data is incomplete and that the deaths in the final bucket are actually
    # decreasing at the same rate as they did from bucket -3 to bucket -2, until
    # there are no deaths left to account for.
    oldest_death_data: list[tuple[int, int]] = list(death_count_by_age.items())[-3:]
    if OPTIMISTIC_MODE and oldest_death_data[-1][1] > oldest_death_data[-2][1]:
        age, remaining_deaths_to_redistribute = oldest_death_data[-1]
        if age != 100:
            raise ValueError("Expected the oldest age to be 100.")
        previous_year_death_count = oldest_death_data[-2][1]  # 5000
        print(
            f"Previous year ({oldest_death_data[-2][0]}) death count:",
            previous_year_death_count,
        )
        # This probably isn't a constant, but glancing at the data between ages
        # 90 to 100, it looks somewhat reasonable to assume as an approximation.
        deaths_per_year_change_rate = (
            oldest_death_data[-2][1] / oldest_death_data[-3][1]
        )  # 0.7
        print("Deaths per year rate of change:", deaths_per_year_change_rate)
        while remaining_deaths_to_redistribute > 0:  # 12000
            print("Remaining deaths to redistribute:", remaining_deaths_to_redistribute)
            # 98 => 5300
            # 99 => 5000
            # 100 => 4700
            # 101 => 4400
            # 102 => 4100
            # 103 => 2900 (remaining)

            this_year_death_count = min(
                remaining_deaths_to_redistribute,
                max(
                    0,
                    int(float(previous_year_death_count) * deaths_per_year_change_rate),
                ),
            )

            print("Adding", this_year_death_count, "deaths at age", age)
            death_count_by_age[age] = this_year_death_count

            remaining_deaths_to_redistribute -= this_year_death_count
            print("remaining deaths to redistribute:", remaining_deaths_to_redistribute)
            previous_year_death_count = this_year_death_count
            age += 1

            if age > 110:
                break

    return death_count_by_age


def graph(min_age: int, data_path: str, include_distribution=False):
    death_count_by_age = get_data(min_age=min_age, data_path=data_path)
    # Create data from the histogram
    ages = np.array(list(death_count_by_age.keys()))
    death_counts = np.array(list(death_count_by_age.values()))
    n = death_counts.sum()
    # Plot the histogram
    plt.title(f"{data_path} from age {min_age}")
    plt.bar(ages, death_counts, color="lightblue")
    plt.xlabel("Age of death")
    plt.ylabel(f"Number of deaths per {n:,} people")

    mean = np.average(ages, weights=death_counts)
    variance = np.average((ages - mean) ** 2, weights=death_counts)
    standard_deviation = np.sqrt(variance)

    # Add sigma label to the plot
    left_shift = 0
    plt.text(
        # How far from the left of the plot
        (ages.max() - ages.min()) * left_shift + ages.min(),
        # How far from the bottom of the plot
        death_counts.max() * 0.6,
        f"$\mu = {mean:.1f}$ years\n"
        f"$\sigma = {standard_deviation:.1f}$ years\n"
        f"$n = {n:,}$ people",
    )

    if include_distribution:
        # NB: This distribution is a total guess, and it's not even a good guess.
        #   Best to just use the PDF of the histogram of past data, not a poor
        #   mathematical approximation.
        distribution_x_vals = np.linspace(start=ages.min(), stop=ages.max(), num=200)
        distribution_y_vals = skewnorm.pdf(
            distribution_x_vals, a=0.9, loc=mean, scale=standard_deviation
        )
        # Plot distribution on the right axis
        right_axis = plt.twinx()
        right_axis.plot(distribution_x_vals, distribution_y_vals, color="red")
        right_axis.legend(["estimated distribution"], loc="best", frameon=False)

    # Create some reconstituted/simulated data to represent each death per year,
    # since the government only gave us a summary histogram of deaths.
    # NB: We add half a year to every age to make the distribution account for
    # the fact that people die, on average in the middle of their age. This is
    # likely not quite true. For example, as we get closer to 100 years old,
    # it's probably more likely that we die at the beginning of our age year than
    # at the end of our age year. But this is a good enough approximation.
    # If we wanted to be pessimistic, we would get rid of this bonus.
    reconstituted_death_ages = np.repeat(
        ages + (0.5 if OPTIMISTIC_MODE else 0), death_counts
    )
    # Calculate and show the percentiles of death ages
    percentiles = [
        np.percentile(reconstituted_death_ages, q=percentile)
        for percentile in PERCENTILES
    ]
    for percentile, color in zip(percentiles, PERCENTILE_COLORS):
        plt.bar(percentile, height=death_counts.max() * 0.5, color=color, width=0.4)
    plt.legend(
        [
            "Actual deaths per age",
            *[
                f"{name}th percentile age of death: {value:.1f}"
                for value, name in zip(percentiles, PERCENTILES)
            ],
        ],
        loc="best",
        frameon=False,
    )

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-path",
        "-d",
        type=str,
        help="This must be the path to a compatible data source. For now only CSV files are supported. See the `data` directory for examples.",
        default="./data/us-total-population.csv",
    )
    parser.add_argument(
        "--min-age",
        "-m",
        type=int,
        default=0,
        help="Data from people who died below this age will be removed from the dataset before analysis.",
    )
    parser.add_argument(
        "--no-distribution",
        action="store_true",
        help="Pass this flag if you want to skip the distribution.",
    )
    options = parser.parse_args()

    graph(
        min_age=options.min_age,
        data_path=options.data_path,
        include_distribution=not options.no_distribution,
    )
