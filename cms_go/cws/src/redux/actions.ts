import type { State } from "./state";

export enum ActionType {
    PatchState,
};

export type Action =
 | { type: ActionType.PatchState; payload: Partial<State>}
