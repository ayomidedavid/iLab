-- Add columns for Mouse, Keyboard, and Power Pack to the assets table
ALTER TABLE assets
  ADD COLUMN mouse VARCHAR(50) AFTER status,
  ADD COLUMN keyboard VARCHAR(50) AFTER mouse,
  ADD COLUMN power_pack VARCHAR(50) AFTER keyboard;
