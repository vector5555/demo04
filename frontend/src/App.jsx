import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import BasicLayout from './layouts/BasicLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/admin/Users';
import Roles from './pages/admin/Roles';
import RoleUser from './pages/admin/RoleUser';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<BasicLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="admin">
            <Route path="users" element={<Users />} />
            <Route path="roles" element={<Roles />} />
            <Route path="role-user" element={<RoleUser />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;