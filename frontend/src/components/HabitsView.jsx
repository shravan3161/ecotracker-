import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';

export default function HabitsView({ userId, onRefreshDashboard, onShowToast }) {
  const storageKey = `ecotracker_custom_habits_${userId || 'default_customer'}`;

  // Load custom habits for this specific user
  const [habits, setHabits] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    // Personalized initial starter set that can be completely deleted or edited
    return [
      {
        id: 'habit_1',
        icon: '🚶',
        title: 'Walk or Cycle Short Trips',
        category: 'transit',
        desc: 'Walking or biking for errands under 3 km instead of taking a car',
        savedKg: 1.20,
        timesLogged: 0
      },
      {
        id: 'habit_2',
        icon: '🥗',
        title: 'Meat-Free Plant Lunch',
        category: 'diet',
        desc: 'Choosing a lentil, bean, or tofu-based meal over red meat',
        savedKg: 1.80,
        timesLogged: 0
      }
    ];
  });

  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('transit');
  const [newIcon, setNewIcon] = useState('🚲');
  const [newSavedKg, setNewSavedKg] = useState('1.5');
  const [newDesc, setNewDesc] = useState('');

  // Persist habits to localStorage when updated
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(habits));
    } catch (e) {
      console.error(e);
    }
  }, [habits, storageKey]);

  const quickEmojis = ['🚶', '🚲', '🥗', '☕', '⚡', '☀️', '💧', '🧺', '🛍️', '🍎', '🚆', '🍃'];

  const categoryPresets = {
    transit: { label: 'Transit & Mobility', defaultKg: 1.5, emoji: '🚲' },
    diet: { label: 'Food & Nutrition', defaultKg: 1.8, emoji: '🥗' },
    appliances: { label: 'Home Appliances', defaultKg: 0.6, emoji: '❄️' },
    energy: { label: 'Clean Energy', defaultKg: 1.2, emoji: '☀️' },
    waste: { label: 'Waste & Recycling', defaultKg: 0.3, emoji: '🛍️' }
  };

  const handleCreateHabit = (e) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      onShowToast('⚠️ Please enter a habit title.');
      return;
    }

    const savedVal = parseFloat(newSavedKg) || 1.0;
    const newHabit = {
      id: `habit_${Date.now()}`,
      title: newTitle.trim(),
      category: newCategory,
      icon: newIcon || '🌱',
      desc: newDesc.trim() || `My personal ${newCategory} sustainability habit`,
      savedKg: savedVal,
      timesLogged: 0
    };

    setHabits((prev) => [newHabit, ...prev]);
    onShowToast(`✨ Created custom habit: "${newTitle.trim()}"`);
    setNewTitle('');
    setNewDesc('');
    setIsCreating(false);
  };

  const deleteHabit = (habitId, title) => {
    setHabits((prev) => prev.filter((h) => h.id !== habitId));
    onShowToast(`🗑️ Removed habit: "${title}"`);
  };

  const logHabit = async (habit) => {
    // Fire celebratory confetti
    confetti({
      particleCount: 50,
      spread: 60,
      origin: { y: 0.7 }
    });

    // Update local timesLogged counter
    setHabits((prev) =>
      prev.map((h) => (h.id === habit.id ? { ...h, timesLogged: (h.timesLogged || 0) + 1 } : h))
    );

    try {
      await fetch('/api/log-preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: habit.category || 'lifestyle',
          activity_details: habit.title,
          co2e_kg: 0.0,
          saved_co2e_kg: habit.savedKg || 1.0,
          user_id: userId
        })
      });
      onShowToast(`🎉 Logged: "${habit.title}" (+${habit.savedKg} kg saved!)`);
      onRefreshDashboard();
    } catch (err) {
      console.error(err);
      onShowToast('⚠️ Error logging habit.');
    }
  };

  return (
    <div>
      <div className="modern-card">
        <div className="card-title-row">
          <div>
            <div className="card-title">⚡ My Personalized Habits Studio</div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '15px', marginTop: '4px' }}>
              Habits are unique to each person. Build, track, and 1-click log your own personalized sustainability actions.
            </p>
          </div>
          <button
            className="btn btn-primary"
            style={{ fontSize: '15px', padding: '10px 18px' }}
            onClick={() => setIsCreating(!isCreating)}
          >
            {isCreating ? '✕ Cancel' : '➕ Add Custom Habit'}
          </button>
        </div>

        {/* Custom Habit Creator Form */}
        {isCreating && (
          <form
            onSubmit={handleCreateHabit}
            style={{
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--primary)',
              borderRadius: '16px',
              padding: '24px',
              marginBottom: '28px',
              animation: 'fadeIn 0.2s ease-out'
            }}
          >
            <h3 style={{ fontSize: '18px', fontWeight: 800, marginBottom: '16px', color: 'var(--primary-light)' }}>
              Create Your Personal Sustainability Habit
            </h3>

            <div className="grid-2" style={{ marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
                  Habit Title *
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Refill stainless water bottle, Solar charge laptop..."
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  autoFocus
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
                  Category
                </label>
                <select
                  className="form-input"
                  value={newCategory}
                  onChange={(e) => {
                    const cat = e.target.value;
                    setNewCategory(cat);
                    setNewSavedKg(categoryPresets[cat]?.defaultKg.toString() || '1.0');
                    setNewIcon(categoryPresets[cat]?.emoji || '🌱');
                  }}
                >
                  <option value="transit">🚆 Transit & Commute</option>
                  <option value="diet">🥗 Food & Nutrition</option>
                  <option value="appliances">❄️ Home Appliances</option>
                  <option value="energy">☀️ Renewable Energy</option>
                  <option value="waste">🛍️ Zero-Waste & Packaging</option>
                </select>
              </div>
            </div>

            <div className="grid-2" style={{ marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
                  Choose Emoji Icon
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {quickEmojis.map((emoji) => (
                    <button
                      type="button"
                      key={emoji}
                      onClick={() => setNewIcon(emoji)}
                      style={{
                        fontSize: '22px',
                        padding: '6px 10px',
                        borderRadius: '8px',
                        border: newIcon === emoji ? '2px solid var(--primary)' : '1px solid var(--border-subtle)',
                        background: newIcon === emoji ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-surface)',
                        cursor: 'pointer'
                      }}
                    >
                      {emoji}
                    </button>
                  ))}
                  <input
                    type="text"
                    value={newIcon}
                    onChange={(e) => setNewIcon(e.target.value)}
                    style={{ width: '48px', textAlign: 'center', fontSize: '20px', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', color: 'var(--text-primary)', padding: '4px' }}
                    title="Or type your own emoji"
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
                  Estimated Carbon Avoided per Action (kg CO2e)
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0.05"
                  max="50"
                  className="form-input"
                  value={newSavedKg}
                  onChange={(e) => setNewSavedKg(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '6px' }}>
                Description or Personal Motivation (Optional)
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="Why this habit matters to you (e.g. Saves money, keeps me active, reduces plastic)..."
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setIsCreating(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Save & Add Habit ➔
              </button>
            </div>
          </form>
        )}

        {/* Habits Cards Grid */}
        {habits.length > 0 ? (
          <div className="grid-3">
            {habits.map((h) => (
              <div
                key={h.id}
                className="modern-card"
                style={{
                  marginBottom: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-surface-elevated)',
                  position: 'relative',
                  transition: 'transform 0.15s ease, border-color 0.15s ease'
                }}
              >
                {/* Delete button */}
                <button
                  onClick={() => deleteHabit(h.id, h.title)}
                  title="Remove this habit"
                  style={{
                    position: 'absolute',
                    top: '14px',
                    right: '14px',
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-tertiary)',
                    cursor: 'pointer',
                    fontSize: '16px',
                    padding: '4px'
                  }}
                  onMouseEnter={(e) => (e.target.style.color = '#ef4444')}
                  onMouseLeave={(e) => (e.target.style.color = 'var(--text-tertiary)')}
                >
                  ✕
                </button>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                    <span style={{ fontSize: '36px' }}>{h.icon || '🌱'}</span>
                    <span
                      className="status-badge"
                      style={{ fontSize: '12px', textTransform: 'capitalize' }}
                    >
                      {h.category}
                    </span>
                  </div>

                  <h4 style={{ fontSize: '18px', fontWeight: 800, marginBottom: '6px' }}>{h.title}</h4>
                  <p style={{ fontSize: '14.5px', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: '1.5' }}>
                    {h.desc}
                  </p>
                </div>

                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-tertiary)' }}>
                      {h.timesLogged ? `Logged ${h.timesLogged}x` : 'Not logged yet'}
                    </span>
                    <span
                      className="status-badge"
                      style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', fontWeight: 800 }}
                    >
                      +{h.savedKg} kg Saved
                    </span>
                  </div>

                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', fontSize: '15px' }}
                    onClick={() => logHabit(h)}
                  >
                    ⚡ Log Habit (+{h.savedKg} kg)
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: '60px 20px',
              background: 'var(--bg-surface-elevated)',
              borderRadius: '16px',
              border: '2px dashed var(--border-subtle)'
            }}
          >
            <div style={{ fontSize: '48px', marginBottom: '14px' }}>🌱</div>
            <h3 style={{ fontSize: '20px', fontWeight: 800, marginBottom: '8px' }}>
              No habits configured yet
            </h3>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 20px', fontSize: '15px' }}>
              Everyone's daily routine is different. Click below to add the sustainable actions and green swaps that fit
              your personal lifestyle.
            </p>
            <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
              ➕ Create My First Habit
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
