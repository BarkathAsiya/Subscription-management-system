import React from "react";
import { Navigate } from "react-router-dom";
import { getSavedUser, getToken } from "../api";

export default function ProtectedRoute({ children }) {
  return getToken() && getSavedUser() ? children : <Navigate to="/login" replace />;
}
