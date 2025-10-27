import numpy as np

# Parameters
num_values = 50
min_val = 1
max_val = 500

# Generate logarithmic values between 1 and 500
log_values = np.logspace(np.log10(min_val), np.log10(max_val), 2000)

# Bias weights: strongly favor higher values, but keep small chance for low ones
x = np.linspace(0, 1, len(log_values))
weights = (x ** 4) + 0.001  # steeper bias (x**4 makes small values rarer)
weights /= weights.sum()

# Randomly sample up to 50 unique values
chosen = np.random.choice(log_values, size=num_values, replace=False, p=weights)

# Round to integers and sort
chosen = np.sort(np.unique(np.rint(chosen).astype(int)))

print(chosen)