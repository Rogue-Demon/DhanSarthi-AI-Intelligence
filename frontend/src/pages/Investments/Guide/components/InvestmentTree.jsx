import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Layers } from 'lucide-react'

const TreeNode = ({ node, level = 0, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const hasChildren = node.children && node.children.length > 0

  const getRiskBadge = (risk) => {
    const r = risk?.toLowerCase() || ''
    if (r.includes('low')) return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
    if (r.includes('very high')) return 'bg-rose-500/10 text-rose-500 border-rose-500/30'
    if (r.includes('high')) return 'bg-amber-500/10 text-amber-500 border-amber-500/30'
    return 'bg-blue-500/10 text-blue-500 border-blue-500/30'
  }

  return (
    <div className="flex flex-col gap-2 w-full select-none">
      {/* Node Row */}
      <div
        onClick={() => hasChildren && setIsOpen(!isOpen)}
        className={`flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border transition-all ${
          level === 0
            ? 'bg-primary/10 border-primary/30 text-foreground font-black'
            : level === 1
              ? 'bg-card border-border/80 hover:border-primary/40 font-bold'
              : 'bg-muted/30 border-border/40 hover:bg-muted/60 text-xs font-semibold'
        } ${hasChildren ? 'cursor-pointer' : ''}`}
        style={{ paddingLeft: `${Math.max(0.8, level * 1.5)}rem` }}
      >
        <div className="flex items-center gap-2.5 min-w-[200px]">
          {hasChildren ? (
            <button className="p-0.5 rounded text-text-muted hover:text-foreground transition-colors">
              {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
          ) : (
            <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0 ml-1" />
          )}

          <div className="flex flex-col">
            <span className={`tracking-tight ${level === 0 ? 'text-sm' : 'text-xs'}`}>
              {node.name}
            </span>
            <span className="text-[10px] text-text-muted font-normal line-clamp-1">
              {node.reason}
            </span>
          </div>
        </div>

        {/* Node Right Stats */}
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="text-right">
            <span className="font-bold text-foreground block">
              ₹{Number(node.amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </span>
            <span className="text-[10px] text-text-muted">{node.allocation_percent}% of plan</span>
          </div>

          <span
            className={`text-[10px] font-sans font-bold px-2 py-0.5 rounded-md border ${getRiskBadge(node.risk_level)}`}
          >
            {node.risk_level}
          </span>

          {node.expected_horizon && (
            <span className="hidden sm:inline-block text-[10px] font-sans text-text-muted bg-muted px-2 py-0.5 rounded-md border border-border/50">
              {node.expected_horizon}
            </span>
          )}
        </div>
      </div>

      {/* Children Tree Nodes */}
      <AnimatePresence initial={false}>
        {isOpen && hasChildren && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-col gap-2 pl-3 border-l-2 border-primary/20 ml-3"
          >
            {node.children.map((childNode, index) => (
              <TreeNode
                key={`${childNode.name}-${index}`}
                node={childNode}
                level={level + 1}
                defaultOpen={level < 1}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function InvestmentTree({ treeData }) {
  if (!treeData) return null

  return (
    <div className="w-full bg-background/60 border border-border/80 rounded-2xl p-4 md:p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between pb-2 border-b border-border/60">
        <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
          <Layers className="h-4 w-4 text-primary" /> Interactive Strategy Hierarchy Tree
        </h4>
        <span className="text-[10px] text-text-muted">
          Click any branch node to expand/collapse
        </span>
      </div>

      <TreeNode node={treeData} level={0} defaultOpen={true} />
    </div>
  )
}
