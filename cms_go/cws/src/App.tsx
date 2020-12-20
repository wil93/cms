import React from 'react';
import { useSelector } from 'react-redux';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { getIsLoggedIn } from './redux/selectors';
import { Login } from './fragments/Login';
import { Navbar } from './fragments/Navbar';
import { Sidebar } from './fragments/Sidebar';

function App() {
  const isLoggedIn = useSelector(getIsLoggedIn);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <div className="w-full flex flex-1">
        {isLoggedIn ? (
          <BrowserRouter>
            <Sidebar />

            <Switch>
              <Route exact path="/">
                home
              </Route>

              <Route path="/contest">
                contest
              </Route>

              <Route path="/task">
                task
              </Route>
            </Switch>
          </BrowserRouter>
        ) : (
          <Login />
        )}
      </div>
    </div>
  );
}

export default App;
