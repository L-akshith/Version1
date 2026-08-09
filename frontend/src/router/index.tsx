import { createBrowserRouter, Navigate } from "react-router-dom";

// Layouts
import { AuthLayout } from "../layouts/AuthLayout";
import { MainLayout } from "../layouts/MainLayout";

// Pages
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { DashboardPage } from "../pages/DashboardPage";
import { UsersPage } from "../pages/UsersPage";
import { RolesPage } from "../pages/RolesPage";
import { PapersPage } from "../pages/PapersPage";
import { AuditPage } from "../pages/AuditPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      {
        path: "login",
        element: <LoginPage />,
      },
      {
        path: "register",
        element: <RegisterPage />,
      },
    ],
  },
  {
    element: <MainLayout />,
    children: [
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "papers",
        element: <PapersPage />,
      },
      {
        path: "users",
        element: <UsersPage />,
      },
      {
        path: "roles",
        element: <RolesPage />,
      },
      {
        path: "audit",
        element: <AuditPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;
