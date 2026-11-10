-- Usuwa dane TESTOWE (użytkownicy t_* z testów i reg_* z regresji) wraz z ich wątkami, zadaniami, audytem, zużyciem i punktami kontrolnymi.
-- Użytkownicy szkoleniowi (ala, bartek, celina) zostają. Uruchomić rolą usługi lub właściciela: psql ... -f cleanup_test_data.sql
BEGIN;
CREATE TEMP TABLE test_users ON COMMIT DROP AS SELECT user_id FROM svc.users WHERE username ~ '^(t|reg)_[0-9a-f]+$';
CREATE TEMP TABLE test_threads ON COMMIT DROP AS SELECT thread_id::text AS tid FROM svc.threads WHERE owner_id IN (SELECT user_id FROM test_users);
DELETE FROM svc.checkpoint_writes WHERE thread_id IN (SELECT tid FROM test_threads);
DELETE FROM svc.checkpoint_blobs  WHERE thread_id IN (SELECT tid FROM test_threads);
DELETE FROM svc.checkpoints       WHERE thread_id IN (SELECT tid FROM test_threads);
DELETE FROM svc.tasks WHERE requester_id IN (SELECT user_id FROM test_users) OR approver_id IN (SELECT user_id FROM test_users);
DELETE FROM svc.threads WHERE owner_id IN (SELECT user_id FROM test_users);       -- wiadomości znikają kaskadowo
DELETE FROM svc.audit_log WHERE actor_id IN (SELECT user_id FROM test_users);
DELETE FROM svc.usage_daily WHERE user_id IN (SELECT user_id FROM test_users);
DELETE FROM svc.users WHERE user_id IN (SELECT user_id FROM test_users);
COMMIT;
