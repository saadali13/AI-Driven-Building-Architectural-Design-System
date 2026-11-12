import React from 'react';
import { Shield, Check, X, KeyRound, Users } from 'lucide-react';

export const RolesManagementPage: React.FC = () => {
  const permissions = [
    { name: 'Synthesize AI Residential Floor Plans', customer: true, architect: true, contractor: true, admin: true },
    { name: 'Export DXF & Architectural PDF Packages', customer: true, architect: true, contractor: true, admin: true },
    { name: 'Approve & Redline PCATP Reviews', customer: false, architect: true, contractor: false, admin: true },
    { name: 'Configure Regional Material Benchmark Rates', customer: false, architect: false, contractor: true, admin: true },
    { name: 'Manage System Users & Permissions Matrix', customer: false, architect: false, contractor: false, admin: true },
    { name: 'Reset Sandbox Demo Telemetry', customer: false, architect: false, contractor: false, admin: true },
  ];

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      <div className="border-b border-[#E2E7E1] pb-5">
        <h1 className="text-2xl font-bold text-[#202923] font-heading">Role & Permission Matrix</h1>
        <p className="text-xs text-[#68736C] mt-1">
          RBAC governance matrix defining platform capabilities across Homeowner, Architect, Contractor, and Admin.
        </p>
      </div>

      <div className="bg-white border border-[#E2E7E1] rounded-3xl p-6 text-xs shadow-xs space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#E2E7E1] text-[#68736C] text-[11px]">
                <th className="pb-3 font-medium">Capability / Permission</th>
                <th className="pb-3 font-medium text-center">Homeowner</th>
                <th className="pb-3 font-medium text-center">PCATP Architect</th>
                <th className="pb-3 font-medium text-center">Contractor</th>
                <th className="pb-3 font-medium text-center">Administrator</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E7E1] text-[#68736C]">
              {permissions.map((p, idx) => (
                <tr key={idx} className="hover:bg-[#F7F7F2]/60 transition-colors">
                  <td className="py-3.5 font-semibold text-[#202923]">{p.name}</td>
                  <td className="py-3.5 text-center">
                    {p.customer ? <Check className="h-4 w-4 text-[#23483D] mx-auto" /> : <X className="h-4 w-4 text-[#68736C]/40 mx-auto" />}
                  </td>
                  <td className="py-3.5 text-center">
                    {p.architect ? <Check className="h-4 w-4 text-[#23483D] mx-auto" /> : <X className="h-4 w-4 text-[#68736C]/40 mx-auto" />}
                  </td>
                  <td className="py-3.5 text-center">
                    {p.contractor ? <Check className="h-4 w-4 text-[#23483D] mx-auto" /> : <X className="h-4 w-4 text-[#68736C]/40 mx-auto" />}
                  </td>
                  <td className="py-3.5 text-center">
                    {p.admin ? <Check className="h-4 w-4 text-[#23483D] mx-auto" /> : <X className="h-4 w-4 text-[#68736C]/40 mx-auto" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
