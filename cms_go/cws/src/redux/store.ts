import { createStore } from "redux";
import { rootReducer } from "./reducer";

const store = createStore(
    rootReducer,
    JSON.parse(localStorage.getItem('reduxState') ?? '{}'),
    // @ts-ignore
    typeof window.__REDUX_DEVTOOLS_EXTENSION__ === 'function' ? window.__REDUX_DEVTOOLS_EXTENSION__() : undefined,
);

store.subscribe(() => localStorage.setItem('reduxState', JSON.stringify(store.getState())));

export { store };
