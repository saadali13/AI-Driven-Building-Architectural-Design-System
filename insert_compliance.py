target_file = 'frontend/src/pages/designs/NewDesignPage.tsx'
with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

compliance_code = """          {/* REQUIREMENTS COMPLIANCE CHECKLIST */}
          {backendDesign?.compliance_checklist && (
            <div className="bg-white border border-[#E2E7E1] rounded-2xl p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-[#E2E7E1] pb-2.5">
                <div className="flex items-center gap-2">
                  <CheckSquare className="h-4 w-4 text-[#23483D]" />
                  <h3 className="font-bold text-xs text-[#202923] uppercase tracking-wider">
                    Requirements Compliance Checklist
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                    backendDesign.compliance_checklist.all_passed
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}>
                    {backendDesign.compliance_checklist.score_pct}% Match ({backendDesign.compliance_checklist.passed_count}/{backendDesign.compliance_checklist.total_count} Passed)
                  </span>
                </div>
              </div>

              {/* USER STATED REQUIREMENTS */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-bold text-[#23483D] uppercase tracking-wider block">
                  User Stated Requirements:
                </span>
                <div className="divide-y divide-[#E2E7E1] max-h-[140px] overflow-y-auto pr-1 text-xs">
                  {(backendDesign.compliance_checklist.requested_items || backendDesign.compliance_checklist.items || []).map((item: any, idx: number) => (
                    <div key={idx} className="py-1.5 flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <span className="font-semibold text-[#202923] text-[11px]">{item.name}</span>
                        <p className="text-[10px] text-[#68736C]">
                          Req: <span className="font-medium text-[#202923]">{item.requested}</span> &rarr; Delivered: <span className="font-medium text-[#202923]">{item.delivered}</span>
                        </p>
                        {item.detail && <p className="text-[9px] text-[#8C9890]">{item.detail}</p>}
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shrink-0 mt-0.5 ${
                        item.status === 'PASS'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'PARTIAL'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* ADDED BY BYLAWS / DEFAULTS */}
              {backendDesign.compliance_checklist.bylaw_defaults && backendDesign.compliance_checklist.bylaw_defaults.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-[#E2E7E1]">
                  <span className="text-[10px] font-bold text-[#68736C] uppercase tracking-wider block">
                    Added by Bylaws / Engineering Defaults:
                  </span>
                  <div className="divide-y divide-[#E2E7E1] max-h-[120px] overflow-y-auto pr-1 text-xs">
                    {backendDesign.compliance_checklist.bylaw_defaults.map((bItem: any, idx: number) => (
                      <div key={idx} className="py-1 flex items-start justify-between gap-2">
                        <div className="space-y-0.5">
                          <span className="font-semibold text-[#202923] text-[11px]">{bItem.name}</span>
                          <p className="text-[10px] text-[#68736C]">{bItem.delivered}</p>
                          <p className="text-[9px] text-[#8C9890] italic">{bItem.statutory_role}</p>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shrink-0 mt-0.5 bg-blue-50 text-blue-700 border border-blue-200">
                          {bItem.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

"""

marker = '{/* DEDICATED REGENERATE & REFINE OVERLAY PAGE */}'
if marker in content:
    content = content.replace(marker, compliance_code + marker, 1)
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Inserted compliance checklist successfully!')
else:
    print('Marker not found!')

