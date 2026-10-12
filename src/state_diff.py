
class StateDiff:
    """Compare saved cloud state with current cloud state."""

    @staticmethod
    def compare_states(saved_state, current_state):
        """Return the differences between two states."""

        differences = {}

        all_keys = set(saved_state) | set(current_state)

        for key in all_keys:
            old_value = saved_state.get(key)
            new_value = current_state.get(key)

            if old_value != new_value:
                differences[key] = {
                    "old": old_value,
                    "new": new_value,
                }

        return differences
