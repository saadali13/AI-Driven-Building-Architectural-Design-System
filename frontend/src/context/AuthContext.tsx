import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { INITIAL_USERS } from '../data/mockData';

interface AuthContextType {
  currentUser: User | null;
  isAuthenticated: boolean;
  login: (email: string, role?: UserRole) => Promise<boolean>;
  signup: (userData: { name: string; email: string; phone: string; role?: UserRole }) => Promise<boolean>;
  logout: () => void;
  switchRole: (role: UserRole) => void;
  updateProfile: (updatedData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'archicraft_user_auth';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch {
      // fallback
    }
    // Default to the Homeowner/Customer for initial exploration
    return INITIAL_USERS[0];
  });

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [currentUser]);

  const login = async (email: string, role?: UserRole): Promise<boolean> => {
    const matched = INITIAL_USERS.find(
      (u) => u.email.toLowerCase() === email.toLowerCase() || (role && u.role === role)
    );
    if (matched) {
      setCurrentUser(matched);
      return true;
    }
    // Demo login: allow any email and default to customer or requested role
    const demoUser: User = {
      id: `usr_${Date.now()}`,
      name: email.split('@')[0].replace(/[._]/g, ' ') || 'Demo User',
      email: email,
      phone: '+92 300 0000000',
      role: role || 'customer',
      createdAt: new Date().toISOString().split('T')[0],
      status: 'active',
    };
    setCurrentUser(demoUser);
    return true;
  };

  const signup = async (userData: { name: string; email: string; phone: string; role?: UserRole }): Promise<boolean> => {
    const newUser: User = {
      id: `usr_${Date.now()}`,
      name: userData.name,
      email: userData.email,
      phone: userData.phone,
      role: userData.role || 'customer', // Public signups are standard customer/homeowner
      createdAt: new Date().toISOString().split('T')[0],
      status: 'active',
    };
    setCurrentUser(newUser);
    return true;
  };

  const logout = () => {
    setCurrentUser(null);
  };

  const switchRole = (newRole: UserRole) => {
    const preset = INITIAL_USERS.find((u) => u.role === newRole);
    if (preset) {
      setCurrentUser(preset);
    } else if (currentUser) {
      setCurrentUser({ ...currentUser, role: newRole });
    }
  };

  const updateProfile = (updatedData: Partial<User>) => {
    if (currentUser) {
      setCurrentUser({ ...currentUser, ...updatedData });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        login,
        signup,
        logout,
        switchRole,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
