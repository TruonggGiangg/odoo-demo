-- Add missing columns to p2p_loan table
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "contractId" VARCHAR;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "willing" TEXT;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "maturity_date" DATE;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "capital" NUMERIC;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "created_date" DATE;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_principal_pay" NUMERIC;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_interest_pay" NUMERIC;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "monthly_pay" NUMERIC;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "entirely_pay" NUMERIC;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "total_notes" INTEGER;
ALTER TABLE p2p_loan ADD COLUMN IF NOT EXISTS "invested_notes" INTEGER;

-- Update existing records
UPDATE p2p_loan SET "contractId" = loan_id WHERE "contractId" IS NULL OR "contractId" = '';
