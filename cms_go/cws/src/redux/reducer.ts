import { ActionType } from "./actions";
import type { Action } from "./actions";
import type { State } from "./state";

const initialState: State = {
  token: undefined,
  user: undefined,
};

export function rootReducer(state = initialState, action: Action) {
  switch (action.type) {
    case ActionType.PatchState:
      return {
        ...state,
        ...action.payload,
      };
    default:
      return state;
  }
}
