import { TIER_META } from '../game/engine.js'

// Renders a database item as a throne card (champion) or a challenger card.
export default function ItemCard({ item, variant = 'challenger', wildcard = false, className = '' }) {
  if (!item) return null
  const tier = TIER_META[item.tier]
  const classes = [
    'card',
    variant,
    wildcard ? 'wildcard' : '',
    item.tier === 4 ? 'chaos' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes}>
      <span className="tier-badge" style={{ color: tier.accent }}>
        {tier.label}
      </span>
      <div className="role">
        {variant === 'champion' ? (
          <>
            <span className="crown">👑</span> On the throne
          </>
        ) : (
          'Challenger'
        )}
      </div>
      <div className="name">{item.name}</div>
      {(item.year || (item.tags && item.tags.length)) && (
        <div className="meta">
          {item.year ? item.year : ''}
          {item.year && item.tags?.length ? ' · ' : ''}
          {item.tags?.slice(0, 3).join(' · ')}
        </div>
      )}
      {item.note && <div className="note">{item.note}</div>}
    </div>
  )
}
