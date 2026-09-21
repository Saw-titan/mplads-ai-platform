import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

const Layout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeRole, setActiveRole] = useState('ADMIN');
  const [refreshKey, setRefreshKey] = useState(0);
  const navigate = useNavigate();

  const handleDatabaseReseeded = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleSelectProject = (projectId) => {
    if (projectId) {
      navigate(`/audit?id=${projectId}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      <Sidebar
        isCollapsed={isCollapsed}
        toggleSidebar={() => setIsCollapsed(!isCollapsed)}
      />

      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isCollapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <Navbar
          activeRole={activeRole}
          setActiveRole={setActiveRole}
          onDatabaseReseeded={handleDatabaseReseeded}
          onSelectProject={handleSelectProject}
        />

        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet context={{ activeRole, refreshKey }} />
        </main>
      </div>
    </div>
  );
};

export default Layout;
