import swisseph as swe
import os
from datetime import datetime, timedelta, timezone

class Astronomy:
    def __init__(self, ephe_path=None):
        if ephe_path:
            # Set ephemeris path
            # swisseph expects the path to be set.
            swe.set_ephe_path(ephe_path)
            
    def get_julian_day(self, utc_dt):
        """Convert UTC datetime to Julian Day."""
        # swe.julday expects year, month, day, hour (decimal)
        hour_decimal = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_decimal)

    def get_true_solar_time(self, utc_dt, lon):
        """
        Calculate True Solar Time (TST).
        
        Formula: TST = LST - RA_Sun + 12h
        LST (Local Sidereal Time) = GMST + Longitude_Time
        
        Args:
            utc_dt (datetime): UTC datetime
            lon (float): Longitude in degrees (East is positive)
            
        Returns:
            dict: {
                'datetime': datetime object representing TST (year/month/day may differ from UTC),
                'decimal': TST in decimal hours (0-24),
                'equation_of_time': EoT in minutes
            }
        """
        jd = self.get_julian_day(utc_dt)
        
        # 1. Get Greenwich Mean Sidereal Time (in hours)
        gmst = swe.sidtime(jd)
        
        # 2. Get Sun's Right Ascension (RA)
        # FLG_EQUATORIAL gives RA in index 0 (degrees), Declination in index 1
        # We need true position, so we typically use FLG_SWIEPH
        flags = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
        res, _ = swe.calc_ut(jd, swe.SUN, flags)
        ra_deg = res[0]
        ra_hours = ra_deg / 15.0
        
        # 3. Calculate Local Sidereal Time
        lon_hours = lon / 15.0
        lst = gmst + lon_hours
        
        # 4. Calculate True Solar Time
        # TST = LHA_Sun + 12h
        # LHA_Sun = LST - RA_Sun
        tst_hours = lst - ra_hours + 12.0
        
        # Normalize to 0-24
        tst_hours = tst_hours % 24.0
        if tst_hours < 0:
            tst_hours += 24.0
            
        # Calculate Equation of Time (EoT) for reference
        # Mean Solar Time = UTC + Lon_Offset
        mean_solar_time = (utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0 + lon_hours) % 24.0
        eot_hours = tst_hours - mean_solar_time
        # Handle wrap around
        if eot_hours > 12: eot_hours -= 24
        if eot_hours < -12: eot_hours += 24
        
        # Construct TST datetime
        # We need to figure out the day. Since TST is close to Mean Solar Time, 
        # we can just apply the offset to the UTC time's base date, 
        # but boundary conditions (around midnight) are tricky.
        # A safer way: TST is roughly UTC + lon_hours.
        # Let's assume the date is the same as "Local Mean Time" date.
        
        # Convert TST decimal hours to HH:MM:SS
        h = int(tst_hours)
        m = int((tst_hours - h) * 60)
        s = int(((tst_hours - h) * 60 - m) * 60)
        
        # Determine the date offset relative to UTC
        # If UTC is 23:00 and TST is 00:30, it's next day.
        # If UTC is 00:30 and TST is 23:00, it's prev day (depending on longitude).
        # We use the approximate offset (lon/15) to guess the day shift.
        base_time = utc_dt.hour + utc_dt.minute/60.0
        approx_local = base_time + lon_hours
        day_shift = 0
        if approx_local >= 24:
            day_shift = 1
        elif approx_local < 0:
            day_shift = -1
        
        # Refine day shift if TST crossed midnight differently than Mean Time?
        # Usually they are within 16 minutes. So the day shift from Mean Time is reliable.
        # However, if Mean Time is 23:55 and TST is 00:10 (EoT +15m), day changes.
        
        # Precise way:
        # Compare TST with Mean Solar Time.
        # If Mean is 23:50 and TST is 00:05, TST is ahead -> next day.
        # If Mean is 00:05 and TST is 23:50, TST is behind -> prev day.
        
        mst_decimal = (base_time + lon_hours) % 24.0
        # Check wrap around difference
        diff = tst_hours - mst_decimal
        if diff > 12: diff -= 24
        if diff < -12: diff += 24
        
        # Logic:
        # Local Mean Date/Time = UTC + lon_offset
        # True Solar Date/Time = Local Mean Date/Time + EoT
        
        utc_timestamp = utc_dt.replace(tzinfo=timezone.utc).timestamp()
        # Add longitude offset (seconds)
        mean_local_timestamp = utc_timestamp + (lon * 240) # 4 min per degree = 240 seconds
        
        # Add EoT (hours * 3600)
        true_solar_timestamp = mean_local_timestamp + (eot_hours * 3600)
        
        tst_dt = datetime.fromtimestamp(true_solar_timestamp, tz=timezone.utc)
        
        return {
            'datetime': tst_dt,
            'decimal': tst_hours,
            'eot_minutes': eot_hours * 60
        }

    def get_solar_terms(self, year):
        """
        Get exact UTC times for 24 solar terms in a given year.
        Solar terms are at ecliptic longitudes 0, 15, 30, ... 345.
        
        Returns:
            dict: {angle (int): datetime (UTC)}
        """
        terms = {}
        # Start searching from end of previous year to cover early terms if needed,
        # but standard is to find terms falling within the year.
        # Usually "Spring Begins" (Li Chun) is around Feb 4 (315 degrees).
        # We need the terms relevant for the months in this year.
        # Let's return a dictionary mapping 0, 15... 345 to the exact time they happen *in or near* this year.
        # Actually, for Bazi, we often need the term covering the date.
        # It's better to search specifically for the term preceding/following a date, 
        # or generate a full list for the year.
        
        # We will generate all 24 terms that occur in this calendar year.
        # Note: A solar term cycle (tropical year) is ~365.24 days.
        # Term 0 (Vernal Equinox) is around March 20.
        
        start_dt = datetime(year, 1, 1, tzinfo=timezone.utc)
        jd_start = self.get_julian_day(start_dt)
        
        # Approximate check every 15 days
        current_jd = jd_start
        for _ in range(26): # Check enough intervals to cover the year
            # Get sun longitude
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            res, _ = swe.calc_ut(current_jd, swe.SUN, flags)
            lon = res[0]
            
            # Find next multiple of 15
            next_target = (int(lon / 15) + 1) * 15
            if next_target >= 360: next_target -= 360
            
            # Estimate when it hits next_target
            # Sun moves ~1 deg/day
            # Distance
            dist = next_target - lon
            if dist < 0: dist += 360
            
            # Jump ahead close to target
            # Use a simple root finding since `swe` is fast
            # We want precise time when lon == target
            
            # Refined search
            target_jd = self._find_crossing(current_jd, next_target)
            
            # Convert target_jd to UTC datetime
            y, m, d, h_decimal = swe.revjul(target_jd)
            h = int(h_decimal)
            mn = int((h_decimal - h) * 60)
            s = int(((h_decimal - h) * 60 - mn) * 60)
            # handle s=60
            if s >= 60:
                s = 0
                mn += 1
            if mn >= 60:
                mn = 0
                h += 1
                
            term_dt = datetime(y, m, d, h, mn, s, tzinfo=timezone.utc)
            
            if term_dt.year == year:
                terms[next_target] = term_dt
            
            current_jd = target_jd + 1 # Move past this term
            
            if len(terms) >= 24 and term_dt.year > year:
                break
                
        return terms

    def _find_crossing(self, start_jd, target_lon):
        """Find the JD when sun longitude is exactly target_lon."""
        # Simple bisection or secant method
        t1 = start_jd
        t2 = start_jd + 20 # Look ahead max 20 days (terms are ~15 days apart)
        
        # Function to get error
        def get_diff(jd):
            res, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
            l = res[0]
            d = l - target_lon
            # Handle 360 wrap: target=0, l=359 -> d=-1. target=0, l=1 -> d=1
            if d > 180: d -= 360
            if d < -180: d += 360
            return d
            
        # Refine t2 to ensure it brackets the crossing if possible, 
        # but since we know sun moves forward, we can just step.
        # Actually, using Newton's method with speed is better.
        
        t = t1
        for _ in range(10): # 10 iterations usually enough for minute precision
            res, _ = swe.calc_ut(t, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
            l = res[0]
            speed = res[3] # degree per day
            
            diff = target_lon - l
            if diff > 180: diff -= 360
            if diff < -180: diff += 360
            
            if abs(diff) < 1e-5: # approx 1 second accuracy
                return t
            
            t += diff / speed
            
        return t
