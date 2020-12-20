import { useState } from "react";
import { Link } from "react-router-dom";
import "./Sidebar.css";

function Clock() {
  return (
    <div className="mx-auto my-5 font-semibold">
      <span className="text-gray-500">Server time:</span> <span className="">12:34</span>
    </div>
  )
}

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex flex-col w-full md:w-64 text-gray-700 bg-gray-200 flex-shrink-0">
      <Clock />

      <nav className={`${isOpen ? 'block' : 'hidden'} flex-grow md:block px-4 pb-4 md:pb-0 md:overflow-y-auto`}>
        <Link className="sidebarButton" to="/">Home</Link>
        <Link className="sidebarButton" to="/contest">Contest</Link>
        <Link className="sidebarButton" to="/task">Task</Link>
        <Link className="sidebarButton" to="/contest">Contact</Link>
      </nav>
    </div>
  );
}
