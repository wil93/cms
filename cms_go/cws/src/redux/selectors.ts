import type { State } from "./state";

export const getIsLoggedIn = (state: State) => {
    return state.token !== undefined;
};
